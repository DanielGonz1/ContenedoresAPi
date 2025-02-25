from flask import Flask, request, jsonify, render_template, url_for, redirect, session, flash
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
import sqlite3
from functools import wraps

app = Flask(__name__)
bcript = Bcrypt(app)


app.secret_key = 'clave_adm'
#app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=10)


def conectar_db():
    conn = sqlite3.connect('contenedor.db')
    conn.row_factory = sqlite3.Row
    return conn

def crear_tablas():
    conn = conectar_db()
     # Crear tabla de usuarios
    conn.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL UNIQUE,
                        password TEXT NOT NULL,
                        email TEXT NOT NULL UNIQUE,
                        nombre TEXT,
                        apellido TEXT,
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )''')
    
    # Crear tabla de barcos
    conn.execute('''CREATE TABLE IF NOT EXISTS barcos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                matricula TEXT NOT NULL,
                capacidad INTEGER,
                numero_pisos INTEGER
                visible BOOLEAN DEFAULT 1
                    )''')
    
    # Crear tabla de contenedores
    conn.execute('''CREATE TABLE IF NOT EXISTS contenedores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    numero TEXT NOT NULL UNIQUE,
                    tipo TEXT,
                    estado TEXT,
                    capacidad INTEGER,
                    visible BOOLEAN DEFAULT 1
                )''')
    
    #crear tabla de puertos
    conn.execute('''CREATE TABLE IF NOT EXISTS puertos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                pais TEXT NOT NULL
                )''')
    
    # crear tabla de envios
    conn.execute('''CREATE TABLE IF NOT EXISTS envios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                puerto_origen_id INTEGER,
                puerto_destino_id INTEGER,
                fecha_salida DATE,
                fecha_llegada DATE,
                pedido_id INTEGER,
                estado TEXT DEFAULT 'Enviado',
                FOREIGN KEY (puerto_origen_id) REFERENCES puertos(id),
                FOREIGN KEY (puerto_destino_id) REFERENCES puertos(id)
                )''')
    
    #creacion de detalles de envio
    conn.execute('''CREATE TABLE IF NOT EXISTS pedido (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contenedor_id INTEGER,
                mercancia TEXT,
                barco_id INTEGER,
                piso_id INTEGER,
                estado TEXT DEFAULT 'Preparacion',
                FOREIGN KEY (barco_id) REFERENCES barco(id),
                FOREIGN KEY (contenedor_id) REFERENCES contenedores(id),
                FOREIGN KEY (piso_id) REFERENCES pisos(id))
                ''')
    
    #crear tabla para los pisos del barco
    conn.execute('''CREATE TABLE IF NOT EXISTS pisos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                barco_id INTEGER NOT NULL,
                capacidad INTEGER,
                FOREIGN KEY (barco_id) REFERENCES barcos(id)
                )''')
    
    conn.execute('''CREATE TABLE IF NOT EXISTS notificaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            mensaje TEXT NOT NULL,
            fecha DATETIME DEFAULT CURRENT_TIMESTAMP,
            leida BOOLEAN DEFAULT 0,
            FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
            )
                ''')
    conn.commit()

    conn.close()

crear_tablas()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash({'message': f'Tu sesión ha expirado. Por favor, inicia sesión nuevamente.', 'type': 'warning'}, "adverted")
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        conn = conectar_db()
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        
        if user and user['is_admin']:
            return f(*args, **kwargs)
        flash({'message': 'Acceso denegado. Solo los administradores pueden acceder a esta página.', 'type': 'warning'}, 'warning')
        return redirect(url_for('dashboard'))
    
    return decorated_function

@app.context_processor
def inject_user():
    if 'user_id' in session:
        try:
            conn = conectar_db()
            user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

            # Obtener notificaciones no leídas
            notificaciones_no_leidas = conn.execute('SELECT COUNT(*) FROM notificaciones WHERE usuario_id = ? AND leida = 0', (session['user_id'],)).fetchone()[0]

            conn.close()

            if user:
                return {
                    'current_user': user,
                    'notificaciones_no_leidas': notificaciones_no_leidas
                }
        except Exception as e:
            print(f"Error fetching user or notifications: {e}")
    return {'notificaciones_no_leidas': 0}


@app.route("/")
def home():
    actualizar_envios()
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/dashboard")
@login_required
def dashboard():

    con = conectar_db()
    user = con.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
    notificaciones = con.execute('SELECT * FROM notificaciones WHERE usuario_id = ? AND leida = 0 ORDER BY fecha DESC', (session['user_id'],)).fetchall()
    total_contenedores = con.execute('SELECT COUNT(*) FROM contenedores WHERE visible = 1').fetchone()[0]
    total_barcos = con.execute('SELECT COUNT(*) FROM barcos WHERE visible = 1').fetchone()[0]
    pedidos_pendientes = con.execute('SELECT COUNT(*) FROM pedido WHERE estado != "Completado"').fetchone()[0]
    total_envios = con.execute('SELECT COUNT(*) FROM envios').fetchone()[0]
    
    envios_completados = con.execute("SELECT COUNT(*) FROM envios WHERE estado='Completado'").fetchone()[0]
    
    if total_envios > 0:
        progreso_envios = round((envios_completados / total_envios) * 100)
    else:
        progreso_envios = 0

    mercancias = con.execute('''SELECT mercancia, COUNT(*) as cantidad
    FROM pedido
    GROUP BY mercancia
            ''').fetchall()

    notificaciones_no_leidas = con.execute('SELECT COUNT(*) FROM notificaciones WHERE usuario_id = ? AND leida = 0', (session['user_id'],)).fetchone()[0]

    con.close()

    total_pedidos = sum(item['cantidad'] for item in mercancias)
    porcentajes = {item['mercancia']: (item['cantidad'] / total_pedidos * 100) if total_pedidos > 0 else 0 for item in mercancias}
    
    if user:
        return render_template('index.html',
                                username=user['username'],
                                nombre=user['nombre'],
                                tcontenedores = total_contenedores,
                                tbarcos = total_barcos,
                                penvios = progreso_envios,
                                ppendientes = pedidos_pendientes,
                                porcentajes = porcentajes,
                                notificaciones = notificaciones,
                                notificaciones_no_leidas=notificaciones_no_leidas)
    else:
        return redirect(url_for('login'))

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        usern = request.form['username']
        passdw = request.form['password']
        conn = conectar_db()
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (usern, )).fetchone()
        conn.close()
        
        if user and bcript.check_password_hash(user['password'], passdw):
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        else:
            flash({'message': 'Credenciales incorrectas.', 'type': 'danger'}, 'error')
    return render_template('login.html', hide_sidebar=True, hide_topbar=True)

@app.route('/registro', methods = ['GET', 'POST'])
@admin_required
def registro():
    if request.method == 'POST':
        nombre = request.form['firsname']
        apellido = request.form['lastname']
        username = request.form['username']
        correo = request.form['email']
        contra = request.form['passd2']
        hashed_password = bcript.generate_password_hash(contra)

        conn = conectar_db()
        try:
            conn.execute('''
                INSERT INTO usuarios (username, password, email, nombre, apellido)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, hashed_password, correo, nombre, apellido))
            conn.commit()
            #flash({'message': 'Usuario registrado exitosamente!', 'type': 'success', 'username': username}, 'success')
            flash({'message': f'Usuario registrado exitosamente!\nUsername: {username}', 'type': 'success'}, 'success')
            return redirect(url_for('users'))
        except sqlite3.IntegrityError:
            flash({'message': 'Error al registrar el usuario.', 'type': 'danger'}, 'error')
        finally:
            conn.close()
    return render_template('register.html', action='register', user={})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/users')
@admin_required
def users():
    conn = conectar_db()
    users = conn.execute('SELECT * FROM usuarios WHERE visible = 1').fetchall()
    conn.close()
    return render_template('usuarios.html', users=users)

@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    conn = conectar_db()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    if request.method == 'POST':
        nombre = request.form['firsname']
        apellido = request.form['lastname']
        username = request.form['username']
        correo = request.form['email']
        contra = request.form['passd2']
        admin = request.form['role']
        
        # Solo actualiza la contraseña si se proporcionó una nueva
        if contra:
            hashed_password = bcript.generate_password_hash(contra)
            conn.execute('''
                UPDATE usuarios SET username = ?, password = ?, email = ?, nombre = ?, apellido = ?, is_admin = ?
                WHERE id = ?
            ''', (username, hashed_password, correo, nombre, apellido, admin, user_id))
        else:
            conn.execute('''
                UPDATE usuarios SET username = ?, email = ?, nombre = ?, apellido = ?, is_admin = ?
                WHERE id = ?
            ''', (username, correo, nombre, apellido, admin, user_id))
        
        conn.commit()
        flash({'message': f'Usuario {username} actualizado exitosamente', 'type': 'success'}, 'success')
        return redirect(url_for('users'))
    
    conn.close()
    return render_template('register.html', action='edit', user=user, hide_sidebar=True, hide_topbar=True)

@app.route('/delete_user/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    conn = conectar_db()
    conn.execute('UPDATE usuarios SET visible = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    flash({'message': 'El usuario se ha eliminado con exito', 'type': "warning"})
    return jsonify({'success': True})

@app.route('/validarUser', methods=['POST'])
def check_username():
    data = request.json
    base_username = data.get('username')
    username = base_username
    count = 1

    conn = conectar_db()
    user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()

    while user is not None:
        username = f"{base_username}{count}"
        user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
        count += 1

    conn.close()
    return jsonify(username=username)

@app.route('/newcontent', methods = ['GET', 'POST'])
@login_required
def contenedores():
    if request.method == 'POST':
        numero = request.form.get('numero')
        tipo = request.form.get('tipo')
        capacidad = request.form.get('peso')

        con = conectar_db()

        try:
            if 'id' in request.form:
                conte_id = request.form.get('id')
                con.execute('''
                    UPDATE contenedores SET tipo = ?, capacidad = ?
                    WHERE id = ?
                ''', (tipo, capacidad, conte_id))
                flash({'message': f'Contenedor M-{numero} actualizado exitosamente', 'type': 'success'}, 'success')
            else:
                con.execute('''
                    INSERT INTO contenedores (numero, tipo, capacidad)
                    VALUES (?, ?, ?)
                ''',(numero, tipo, capacidad))
                flash({'message': f'Se ha registrado el contenedor con número M-{numero}', 'type': 'success'}, 'success')
            con.commit()
        except Exception as e:
            con.rollback()
            flash({'message': f'Error al agregar el contenedor: {str(e)}', 'type': 'danger'}, 'danger')
        finally:
            con.close()
        return redirect(url_for('explorarC'))
    return render_template('nueCont.html', conte={}, action='nuevo')

@app.route('/contenedores', methods = ['GET'])
@login_required
def explorarC():
    conn = conectar_db()
    conte = conn.execute('SELECT * FROM contenedores WHERE visible = 1').fetchall()
    conn.close()
    return render_template('contenedores.html', conte = conte)

@app.route('/delete_conte/<int:conte_id>', methods=['DELETE'])
@login_required
def delete_conte(conte_id):
    conn = conectar_db()
    conn.execute('UPDATE contenedores SET visible = 0 WHERE id = ?', (conte_id,))
    conn.commit()
    conn.close()
    flash({'message': 'El contenedor se ha eliminado con exito', 'type': "warning"})
    return jsonify({'success': True})

@app.route('/edit_cont/<int:conte_id>', methods=['GET', 'POST'])
@admin_required
def edit_cont(conte_id):
    conn = conectar_db()
    conte = conn.execute('SELECT * FROM contenedores WHERE id = ?', (conte_id,)).fetchone()
    conn.close()
    return render_template('nueCont.html', action='edit', conte=conte)

@app.route('/embarcaciones',  methods=['GET'])
@login_required
def explorarE():
    conn = conectar_db()
    barco = conn.execute('SELECT * FROM barcos WHERE visible = 1').fetchall()
    conn.close()
    print(f"no hay nada {barco}") 
    return render_template('embarcaciones.html', barco=barco)

@app.route('/embarques', methods=['GET', 'POST'])
@login_required
def embarques():
    if request.method == 'POST':
        matricula = request.form.get('matricula')
        tamano = request.form.get('tamano')
        npisos = int(request.form.get('numero_pisos'))
        capacidad = int(request.form.get('capacidad'))

        con = conectar_db()

        try:
            # Actualización de un barco
            if 'id' in request.form:
                barco_id = request.form.get('id')
                con.execute('''
                    UPDATE barcos SET tamano = ?, numero_pisos = ?, capacidad = ?
                    WHERE id = ?
                ''', (tamano, npisos, capacidad, barco_id))
                flash({'message': f'El barco E-{matricula} se ha actualizado con éxito', 'type': 'success'}, 'success')

                # Actualizar capacidad de pisos
                con.execute('DELETE FROM pisos WHERE barco_id = ?', (barco_id,))
                capacidad_p = capacidad // npisos
                for _ in range(npisos):
                    con.execute('''INSERT INTO pisos (barco_id, capacidad)
                                   VALUES (?, ?)''', (barco_id, capacidad_p))
            # Nuevo registro
            else:
                cur = con.cursor()
                cur.execute('''INSERT INTO barcos (matricula, tamano, capacidad, numero_pisos)
                               VALUES (?, ?, ?, ?)''', (matricula, tamano, capacidad, npisos))
                barco_id = cur.lastrowid
                flash({'message': f'Se ha registrado el barco con matrícula E-{matricula}', 'type': 'success'}, 'success')

                # Asignar capacidad por piso
                capacidad_p = capacidad // npisos
                for _ in range(npisos):
                    cur.execute('''INSERT INTO pisos (barco_id, capacidad)
                                   VALUES (?, ?)''', (barco_id, capacidad_p))
            con.commit()
        except sqlite3.IntegrityError as e:
            flash({'message': f'Ocurrió un error: {str(e)}', 'type': 'danger'}, 'error')
        except Exception as e:
            flash({'message': f'Ocurrió un error inesperado: {str(e)}', 'type': 'danger'}, 'error')
        finally:
            con.close()
        return redirect(url_for('explorarE'))

    return render_template('nueEmb.html', barco={}, action='nuevo')


@app.route('/edit_barco/<int:barco_id>', methods=['GET'])
@login_required
def edit_barco(barco_id):
    conn = conectar_db()
    barco = conn.execute('SELECT * FROM barcos WHERE id = ?', (barco_id,)).fetchone()
    conn.close()
    return render_template('nueEmb.html', action='edit', barco=barco)

@app.route('/delete_barco/<int:barco_id>', methods=['DELETE'])
@login_required
def delete_barco(barco_id):
    con=conectar_db()
    con.execute('UPDATE barcos SET visible = 0 WHERE id = ?',(barco_id,))
    con.commit()
    con.execute('DELETE FROM pisos WHERE barco_id = ?', (barco_id,))
    con.commit()
    con.close()
    flash({'message': 'El barco se ha eliminado con exito', 'type': "warning"})
    return jsonify({'success': True})

@app.route('/check_barco_number', methods=['GET'])
@login_required
def check_barco_number():
    numero = request.args.get('numero')
    if not numero or len(numero) < 6:
        return jsonify({'exists': False, 'message': 'Número de contenedor inválido. Debe tener 6 digitos.'})
    
    con = conectar_db()
    barco = con.execute('SELECT 1 FROM barcos WHERE matricula = ?', (numero,)).fetchone()
    con.close()
    
    if barco:
        return jsonify({'exists': True, 'message': 'Matricula de barco ya ocupado.'})
    else:
        return jsonify({'exists': False, 'message': 'Matricula de barco disponible.'})

@app.route('/check_container_number', methods=['GET'])
@login_required
def check_container_number():
    numero = request.args.get('numero')
    if not numero or len(numero) < 6 or len(numero) > 8:
        return jsonify({'exists': False, 'message': 'Número de contenedor inválido. Debe tener entre 6 y 8 dígitos.'})
    
    con = conectar_db()
    contenedor = con.execute('SELECT 1 FROM contenedores WHERE numero = ?', (numero,)).fetchone()
    con.close()
    
    if contenedor:
        return jsonify({'exists': True, 'message': 'Número de contenedor ya ocupado.'})
    else:
        return jsonify({'exists': False, 'message': 'Número de contenedor disponible.'})

@app.route('/pedido', methods = ['GET'])
@login_required
def pedido():
    con = conectar_db()
    conte = con.execute('SELECT id, numero, capacidad FROM contenedores WHERE estado = "Disponible" AND visible = 1')
    barco = con.execute('SELECT id, matricula FROM barcos WHERE (estado = "Disponible" OR estado = "Preparando") AND visible = 1')
    return render_template('pedido.html', conte = conte, barco = barco)

#Me quede aqui

@app.route('/pisos/<int:barco_id>', methods=['GET'])
@login_required
def get_pisos(barco_id):
    con = conectar_db()
    pisos = con.execute('SELECT id, capacidad, capacidad_ocupada FROM pisos WHERE barco_id = ?', (barco_id,))
    pisos_data = []
    for index, piso in enumerate(pisos):
        numero_piso = index + 1  # Enumeración desde 1
        pisos_data.append({
            'id': piso['id'],
            'numero_piso': numero_piso,
            'capacidad': piso['capacidad'],
            'capacidad_ocupada': piso['capacidad_ocupada']
        })
    return jsonify(pisos_data)

@app.route('/contenedor/<int:conte_id>', methods=['GET'])
@login_required
def get_contenedor_capacidad(conte_id):
    con = conectar_db()
    contenedor = con.execute('SELECT capacidad FROM contenedores WHERE id = ?', (conte_id,)).fetchone()
    return jsonify({'capacidad': contenedor['capacidad']})


@app.route('/crear_pedido', methods=['POST'])
@login_required
def crear_pedido():
    con = conectar_db()
    try:
        # Obtener datos del formulario
        conte_id = request.form.get('conte_id')
        merca = request.form.get('merca')
        barco_id = request.form.get('barco_id')
        piso_id = request.form.get('piso_id')

        # Validar datos recibidos
        if not conte_id or not merca or not barco_id or not piso_id:
            flash({'message': 'Todos los campos son obligatorios.', 'type': 'danager'}, 'error')
            return redirect(url_for('pedido'))
        
        capaCo = con.execute('SELECT capacidad FROM contenedores WHERE id = ?', (conte_id,)).fetchone()
        capapiso = con.execute('SELECT capacidad, capacidad_ocupada FROM pisos WHERE id = ?', (piso_id,)).fetchone()
        cpt = capapiso[0]
        cpo = capapiso[1]
        print(f"capacidad: {cpt} y ocupada: {cpo}, disponible: {cpt-cpo}")

        if cpt >= cpo and (cpt - cpo) >= capaCo[0]:
            con.execute(
                'INSERT INTO pedido (contenedor_id, mercancia, barco_id, piso_id) VALUES (?, ?, ?, ?)',
                (conte_id, merca, barco_id, piso_id)
            )
            con.commit()

            # Actualizar el estado del contenedor a 'Asignado'
            con.execute(
                'UPDATE contenedores SET estado = "Asignado" WHERE id = ?',
                (conte_id,)
            )
            con.commit()

            # Actualizar la capacidad ocupada del piso correspondiente
            con.execute(
                'UPDATE pisos SET capacidad_ocupada = capacidad_ocupada + (SELECT capacidad FROM contenedores WHERE id = ?) WHERE id = ?',
                (conte_id, piso_id)
            )
            con.commit()

            con.execute('UPDATE barcos SET estado = "Preparando" WHERE id = ?',(barco_id,))
            con.commit()

            # Verificar si todos los pisos del barco tienen una capacidad disponible menor a 24,000
            pisos = con.execute(
                'SELECT capacidad, capacidad_ocupada FROM pisos WHERE barco_id = ?',
                (barco_id,)
            ).fetchall()
            
            todos_ocupados = all((piso[0] - piso[1]) < 24000 for piso in pisos)

            crear_notificacion_para_todos(con, f'Se ha creado un nuevo pedido para el barco {barco_id} en el piso {piso_id}.')

            if todos_ocupados:
                con.execute(
                    'UPDATE barcos SET estado = "Ocupado" WHERE id = ?',
                    (barco_id,)
                )
                con.commit()

            flash({'message': 'Pedido creado con éxito.', 'type': 'success'}, 'success')

        else:
            flash({'message': 'La capacidad del piso es insuficiente para el contenedor.', 'type': 'danger'}, 'error')

        return redirect(url_for('pedido'))

    except Exception as e:
        con.rollback()
        flash({'message': f'Error al crear el pedido: {str(e)}', 'type': 'danger'}, 'error')
        return redirect(url_for('pedido'))
    finally:
        con.close()

def crear_notificacion_para_todos(con, mensaje):
    usuarios = con.execute('SELECT id FROM usuarios').fetchall()
    for usuario in usuarios:
        con.execute(
            'INSERT INTO notificaciones (mensaje, usuario_id) VALUES (?, ?)',
            (mensaje, usuario['id'])
        )
    con.commit()

def marcar_notificaciones_como_leidas(con, usuario_id):
    con.execute('UPDATE notificaciones SET leida = 1 WHERE usuario_id = ?', (usuario_id,))
    con.commit()


@app.route('/envios', methods=['GET', 'POST'])
@login_required
def envios():
    con = conectar_db()
    if request.method == 'POST':
        puertoO = request.form.get('puertoO')
        puertoD = request.form.get('puertoD')
        barco_id = request.form.get('barco_id')
        fechaS = request.form.get('fecha_salida')
        fechaL = request.form.get('fecha_llegada')
        try:
            print(f"Valores recibidos: puertoO={puertoO}, puertoD={puertoD}, barco_id={barco_id}, fechaS={fechaS}, fechaL={fechaL}")
            pedidos = con.execute('SELECT id, contenedor_id FROM pedido WHERE barco_id = ?', (barco_id,)).fetchall()
            
            if not pedidos:
                raise ValueError("No se encontraron pedidos para el barco seleccionado.")
            
            con.commit()
            for pedido in pedidos:
                con.execute('''INSERT INTO envios (puerto_origen_id, puerto_destino_id, fecha_salida, fecha_llegada, pedido_id)
                            VALUES (?, ?, ?, ?, ?)''', (puertoO, puertoD, fechaS, fechaL, pedido['id']))
                con.commit()
                con.execute('UPDATE pedido set estado = "En transito" WHERE id = ?',(pedido['id'],))
                con.commit()
                con.execute('UPDATE contenedores set estado = "En transito" WHERE id = ?',(pedido['contenedor_id'],))
                con.commit()
            con.execute('UPDATE barcos SET estado = "En transito" WHERE id = ?',(barco_id,))
            con.commit()
            flash({'message': 'Los pedidos se han enviado con exito', 'type': 'success'}, 'success')
        except sqlite3.IntegrityError as e:
            flash({'message': f'Ocurrió un error: {str(e)}', 'type': 'danger'}, 'error')
        except Exception as e:
            flash({'message': f'Ocurrió un error inesperado: {str(e)}', 'type': 'danger'}, 'error')
        finally:
            pass
    cur = con.cursor()
    cur.execute('SELECT * FROM puertos')
    puertos = cur.fetchall()
    barcos = con.execute('SELECT id, matricula FROM barcos WHERE estado = "Ocupado"')
    return render_template('envios.html', puerto = puertos, barco = barcos)

@app.route('/get_pedidos/<int:id_barco>', methods = ['GET'])
@login_required
def get_pedidos(id_barco):
    con = conectar_db()
    pedidos_detallados = []
    pedidos = con.execute('SELECT id, contenedor_id, mercancia FROM pedido WHERE estado = "Preparacion" AND barco_id = ?', (id_barco,)).fetchall()
    for pedido in pedidos:
        contenedor = con.execute('SELECT numero FROM contenedores WHERE id = ?', (pedido['contenedor_id'],)).fetchone()
        pedidos_detallados.append({
            'id': pedido['id'],
            'numeroc': contenedor['numero'] if contenedor else None,
            'contenido': pedido['mercancia']
        })
    con.close()
    return jsonify(pedidos_detallados)

@app.route('/total_pedidos', methods=['GET'])
def obtener_pedidos():
    con = conectar_db()
    cur = con.cursor()
    
    # Consulta para obtener los estados y las cantidades de pedidos
    cur.execute('''
        SELECT estado, COUNT(*) as cantidad
        FROM pedido
        GROUP BY estado
    ''')
    pedidos = cur.fetchall()
    
    # Formatear los datos en un diccionario
    data = [{'estado': pedido[0], 'cantidad': pedido[1]} for pedido in pedidos]
    
    con.close()
    return jsonify(data)

@app.route('/envios_por_mes', methods=['GET'])
def obtener_envios():
    con = conectar_db()
    cur = con.cursor()
    
    cur.execute('''
        SELECT strftime('%Y-%m', fecha_llegada) as mes, COUNT(*) as cantidad
        FROM envios
        WHERE estado = 'Completado'
        GROUP BY mes
        ORDER BY mes
    ''')
    earnings = cur.fetchall()
    
    data = [{'mes': earning[0], 'cantidad': earning[1]} for earning in earnings]
    
    return jsonify(data)


@app.route('/pedidos/<estado>', methods={'GET'})
def pedidos(estado):
    page = request.args.get('page', 1, type=int)
    per_page = 10
    estados_validos = {
        'pendientes':{
            'estado_sql' : 'Preparacion',
            'titulo': 'Pedidos pendientes'
        },
        'en_transito':{
            'estado_sql' : 'En transito',
            'titulo': 'Pedidos en transito'
        },
        'completos':{
            'estado_sql' : 'Completado',
            'titulo': 'Pedidos completos'
        }
    }
    con = conectar_db()
    if estado not in estados_validos:
        return 'Estado no valido', 404
    estado_sql = estados_validos[estado]['estado_sql']
    titulo = estados_validos[estado]['titulo']
    total_pendientes = con.execute('''
        SELECT COUNT(*) FROM pedido
        JOIN contenedores ON pedido.contenedor_id = contenedores.id
        WHERE pedido.estado = ?
        ''', (estado_sql,)).fetchone()[0]
    tipo = con.execute('''
        SELECT pedido.id, pedido.mercancia, contenedores.numero AS contenedor_numero, contenedores.capacidad 
        FROM pedido
        JOIN contenedores ON pedido.contenedor_id = contenedores.id
        WHERE pedido.estado = ?
        LIMIT ? OFFSET ?
    ''', (estado_sql, per_page, (page - 1) * per_page)).fetchall()
    con.close()
    total_pages = (total_pendientes + per_page - 1) // per_page
    return render_template('info_pedidos.html', pen = tipo, titulo = titulo, page = page, total_pages = total_pages, estado = estado)


@app.route('/enviospor', defaults={'page': 1, 'barco_id': None}, methods=['GET', 'POST'])
@app.route('/enviospor/<int:page>/<int:barco_id>', methods=['GET', 'POST'])
def envios_por_barco(page, barco_id):
    con = conectar_db()
    limit = 5
    offset = (page - 1) * limit
    
    # Obtener lista de barcos
    barcos = con.execute('SELECT * FROM barcos').fetchall()
    
    pedidos = []
    total_pedidos = 0
    barco = None
    tipo = 'get'  # Por defecto, asume que es un GET
    
    if request.method == 'POST':
        barco_id = request.form.get('barcos')
        tipo = 'post'  # Cambia a POST cuando se envía el formulario
        page = 1  # Resetea la página a 1 cuando se selecciona un nuevo barco
        return redirect(url_for('envios_por_barco', page=page, barco_id=barco_id))
    
    if barco_id:
        barco_row = con.execute('SELECT matricula FROM barcos WHERE id = ?', (barco_id,)).fetchone()
        if barco_row:
            barco = dict(barco_row)
        
        # Consultar los pedidos relacionados con el barco
        pedidos_rows = con.execute('''
            SELECT p.id as pedido_id, 
                e.id as envio_id, 
                c.numero as contenedor_matricula, 
                b.matricula as barco_matricula, 
                p.piso_id, 
                p.mercancia,
                (SELECT COUNT(*) FROM pisos p2 WHERE p2.id <= p.piso_id AND p2.barco_id = ?) as numero_piso
            FROM pedido p
            JOIN envios e ON p.id = e.pedido_id
            JOIN barcos b ON p.barco_id = b.id
            JOIN contenedores c ON p.contenedor_id = c.id
            WHERE b.id = ?
            LIMIT ? OFFSET ?
        ''', (barco_id, barco_id, limit, offset)).fetchall()



        
        # Convertir filas a diccionarios
        pedidos = [dict(row) for row in pedidos_rows]
        
        # Obtener el total de pedidos
        total_pedidos = con.execute('''
            SELECT COUNT(*)
            FROM pedido p
            JOIN barcos b ON p.barco_id = b.id
            WHERE b.id = ?
        ''', (barco_id,)).fetchone()[0]
    
    total_pages = (total_pedidos + limit - 1) // limit  # Calcula el total de páginas
    
    return render_template(
        'envios_barco.html',
        barcos=barcos,
        tipo=tipo,
        barco=barco,
        pedidos=pedidos,
        total_pedidos=total_pedidos,
        page=page,
        limit=limit,
        total_pages=total_pages,
        barco_id=barco_id
    )

@app.template_filter('capitalize_first')
def capitalize_first(value):
    if not value:
        return ''
    return value[0].upper() + value[1:].lower()

@app.template_filter('capitalize_words')
def capitalize_words(value):
    if not value:
        return ''
    # Capitalizar cada palabra
    return ' '.join([word.capitalize() for word in value.split()])


#               PENDIENTEEEES


@app.route('/forget')
def forgot_password():
    return render_template('forgot-password.html')

@app.route('/404_page')
def page_404():
    return render_template('404.html')

@app.route('/blank')
def blank():
    return render_template('charts.html')

#               Extras

def actualizar_envios():
    con = conectar_db()
    cur = con.cursor()
    fecha_actual = datetime.now().strftime('%Y-%m-%d')
    cur.execute('''
        UPDATE envios
        SET estado = "Completado"
        WHERE fecha_llegada < ?
        AND estado != "Completado"
    ''', (fecha_actual,))
    con.commit()
    envios = con.execute('SELECT pedido_id FROM envios WHERE estado = "Completado"')
    for en in envios:
        con.execute('UPDATE pedido SET estado = "Completado" WHERE id = ?',(en[0],))
        con.commit()
        pedidos = con.execute('SELECT contenedor_id, barco_id, piso_id FROM pedido WHERE id = ?',(en[0],))
        for pe in pedidos:
            con.execute('UPDATE contenedores SET estado = "Disponible" WHERE id = ?',(pe[0],))
            con.commit()
            con.execute('UPDATE barcos SET estado = "Disponible" WHERE id = ?',(pe[1],))
            con.commit()
            con.execute('UPDATE pisos SET capacidad_ocupada = 0 WHERE id = ?',(pe[2],))
    con.close()

if __name__ == '__main__':
    app.run(debug=True)