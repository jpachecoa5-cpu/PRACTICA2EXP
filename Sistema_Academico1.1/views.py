from abc import ABC, abstractmethod

from models import Estudiante, Materia, Matricula
from shared.json_manager import GestorJSON
from shared.herramientas import es_email_valido


class CrudBase(ABC):
    @abstractmethod
    def leer(self):
        pass

    @abstractmethod
    def obtener(self, id_registro):
        pass

    @abstractmethod
    def buscar(self, texto):
        pass

    @abstractmethod
    def siguiente(self):
        pass

    @abstractmethod
    def crear(self, datos):
        pass

    @abstractmethod
    def actualizar(self, id_registro, datos):
        pass

    @abstractmethod
    def eliminar(self, id_registro):
        pass

    def ids_registrados(self):
        # Un conjunto permite comprobar la existencia de ids sin duplicados.
        return {objeto.id for objeto in self.lista}

    def indice_por_id(self):
        return {objeto.id: objeto for objeto in self.lista}


class EstudianteController(CrudBase):

    def __init__(self, archivo="data/estudiantes.json"):
        self.gestor = GestorJSON(archivo)
        self.lista = [
            Estudiante.desde_diccionario(datos)
            for datos in self.gestor.leer()
        ]

    def guardar(self):
        self.gestor.guardar([estudiante.a_diccionario()
                             for estudiante in self.lista])

    def validar(self, datos, id_actual=None):
        for campo in ("nombre", "apellido", "email", "carnet"):
            requerido = id_actual is None or campo in datos
            if requerido and str(datos.get(campo, "")).strip() == "":
                return f"El campo {campo} es obligatorio"

        if "email" in datos:
            email = str(datos["email"]).strip().lower()
            if not es_email_valido(email):
                return f"Email inválido: '{email}'"
            emails = {e.email.lower() for e in self.lista if e.id != id_actual}
            if email in emails:
                return "Ese email ya está registrado"

        if "carnet" in datos:
            carnet = str(datos["carnet"]).strip()
            # El conjunto detecta carnets repetidos, excluyendo el registro editado.
            carnets = {e.carnet.casefold() for e in self.lista if e.id != id_actual}
            if carnet.casefold() in carnets:
                return "Ese carnet ya está registrado"
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_estudiante):
        if id_estudiante not in self.ids_registrados():
            return None
        return next((e for e in self.lista if e.id == id_estudiante), None)

    def buscar(self, texto):
        texto = texto.strip().casefold()
        encontrados = []
        if not texto:
            return encontrados
        # La tupla mantiene juntos los campos buscables sin crear una colección mutable.
        campos = ("nombre", "apellido", "email", "carnet", "carrera")
        for estudiante in self.lista:
            if any(texto in str(getattr(estudiante, campo)).casefold()
                   for campo in campos):
                encontrados.append(estudiante)
        return encontrados

    def siguiente(self):
        return max(self.ids_registrados(), default=0) + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error

        estudiante = Estudiante(
            self.siguiente(),
            str(datos["nombre"]).strip().title(),
            str(datos["apellido"]).strip().title(),
            str(datos["email"]).strip().lower(),
            str(datos["carnet"]).strip(),
            str(datos.get("carrera", "")).strip().title(),
        )
        self.lista.append(estudiante)
        self.guardar()
        # La tupla comunica el resultado y su mensaje como un solo valor.
        return True, f"Estudiante creado: {estudiante.etiqueta()}"

    def actualizar(self, id_estudiante, datos):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        if not datos:
            return False, "No se indicó ningún cambio"

        permitidos = {"nombre", "apellido", "email", "carnet", "carrera"}
        desconocidos = set(datos) - permitidos
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"

        error = self.validar(datos, id_estudiante)
        if error:
            return False, error
        for campo, valor in datos.items():
            valor = str(valor).strip()
            if campo in ("nombre", "apellido", "carrera"):
                valor = valor.title()
            elif campo == "email":
                valor = valor.lower()
            setattr(estudiante, campo, valor)
        self.guardar()
        return True, f"Estudiante {id_estudiante} actualizado"

    def eliminar(self, id_estudiante):
        estudiante = self.obtener(id_estudiante)
        if estudiante is None:
            return False, f"No existe un estudiante con id {id_estudiante}"
        self.lista.remove(estudiante)
        self.guardar()
        return True, f"Estudiante {id_estudiante} eliminado"

    def carreras(self):
        # El conjunto ordenado muestra cada carrera una sola vez.
        return sorted({e.carrera for e in self.lista if e.carrera})


class MateriaController(CrudBase):

    def __init__(self, archivo="data/materias.json"):
        self.gestor = GestorJSON(archivo)
        self.lista = [
            Materia.desde_diccionario(datos)
            for datos in self.gestor.leer()
        ]

    def guardar(self):
        self.gestor.guardar([materia.a_diccionario() for materia in self.lista])

    def validar(self, datos, id_actual=None):
        for campo in ("nombre", "codigo", "creditos"):
            requerido = id_actual is None or campo in datos
            if requerido and str(datos.get(campo, "")).strip() == "":
                return f"El campo {campo} es obligatorio"

        if "codigo" in datos:
            codigo = str(datos["codigo"]).strip()
            # El conjunto hace eficiente detectar códigos ya ocupados.
            codigos = {m.codigo.casefold() for m in self.lista if m.id != id_actual}
            if codigo.casefold() in codigos:
                return "Ese código ya está registrado"

        for campo, minimo, maximo in (
                ("creditos", 1, 10), ("cupos", 0, Materia.CUPOS_MAXIMOS)):
            if campo in datos or (id_actual is None and campo == "cupos"):
                try:
                    valor_original = datos.get(campo, 0)
                    if campo == "cupos" and str(valor_original).strip() == "":
                        valor_original = 0
                    valor = int(valor_original)
                except (TypeError, ValueError):
                    return f"{campo.capitalize()} debe ser un número entero"
                if not minimo <= valor <= maximo:
                    return (f"{campo.capitalize()} debe estar entre "
                            f"{minimo} y {maximo}")
        return None

    def leer(self):
        return self.lista

    def obtener(self, id_materia):
        if id_materia not in self.ids_registrados():
            return None
        return next((m for m in self.lista if m.id == id_materia), None)

    def buscar(self, texto):
        texto = texto.strip().casefold()
        encontrados = []
        if not texto:
            return encontrados
        # Nombre y código son la tupla fija de campos de búsqueda de materias.
        campos = ("nombre", "codigo")
        for materia in self.lista:
            if any(texto in str(getattr(materia, campo)).casefold()
                   for campo in campos):
                encontrados.append(materia)
        return encontrados

    def siguiente(self):
        return max(self.ids_registrados(), default=0) + 1

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        materia = Materia(
            self.siguiente(),
            str(datos["nombre"]).strip().title(),
            str(datos["codigo"]).strip().upper(),
            int(datos["creditos"]),
            int(datos.get("cupos") or 0),
        )
        self.lista.append(materia)
        self.guardar()
        return True, f"Materia creada: {materia.etiqueta()}"

    def actualizar(self, id_materia, datos):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        if not datos:
            return False, "No se indicó ningún cambio"
        desconocidos = set(datos) - {"nombre", "codigo", "creditos", "cupos"}
        if desconocidos:
            return False, f"Campos no válidos: {', '.join(sorted(desconocidos))}"
        error = self.validar(datos, id_materia)
        if error:
            return False, error
        for campo, valor in datos.items():
            if campo in ("creditos", "cupos"):
                valor = int(valor)
            else:
                valor = str(valor).strip()
                if campo == "nombre":
                    valor = valor.title()
                elif campo == "codigo":
                    valor = valor.upper()
            setattr(materia, campo, valor)
        self.guardar()
        return True, f"Materia {id_materia} actualizada"

    def eliminar(self, id_materia):
        materia = self.obtener(id_materia)
        if materia is None:
            return False, f"No existe una materia con id {id_materia}"
        self.lista.remove(materia)
        self.guardar()
        return True, f"Materia {id_materia} eliminada"

    def materias_sin_cupo(self):
        return [materia for materia in self.lista if not materia.hay_cupo()]


class MatriculaController(CrudBase):

    def __init__(self, estudiantes, materias, archivo="data/matriculas.json"):
        self.estudiantes = estudiantes
        self.materias = materias
        self.gestor = GestorJSON(archivo)
        self.lista = [
            Matricula.desde_diccionario(datos)
            for datos in self.gestor.leer()
        ]

    def guardar(self):
        self.gestor.guardar([matricula.a_diccionario()
                             for matricula in self.lista])

    def leer(self):
        return self.lista

    def obtener(self, id_matricula):
        if id_matricula not in self.ids_registrados():
            return None
        return next((m for m in self.lista if m.id == id_matricula), None)

    def buscar(self, texto):
        texto = texto.strip()
        encontrados = []
        if not texto:
            return encontrados
        # Periodo y fecha conforman la tupla fija de campos buscables.
        campos = ("periodo", "fecha")
        for matricula in self.lista:
            if any(texto in str(getattr(matricula, campo)) for campo in campos):
                encontrados.append(matricula)
        return encontrados

    def siguiente(self):
        return max(self.ids_registrados(), default=0) + 1

    def validar(self, datos, id_actual=None):
        try:
            estudiante_id = int(datos.get("estudiante_id", 0))
            materia_id = int(datos.get("materia_id", 0))
        except (TypeError, ValueError):
            return "estudiante_id y materia_id deben ser números enteros"

        if self.estudiantes.obtener(estudiante_id) is None:
            return f"No existe un estudiante con id {estudiante_id}"
        materia = self.materias.obtener(materia_id)
        if materia is None:
            return f"No existe una materia con id {materia_id}"
        periodo = str(datos.get("periodo", "")).strip()
        if not periodo:
            return "El periodo es obligatorio"

        if any(m.id != id_actual
               and m.estudiante_id == estudiante_id
               and m.materia_id == materia_id
               and m.periodo.casefold() == periodo.casefold()
               for m in self.lista):
            return "El estudiante ya está matriculado en esa materia y periodo"
        if not materia.hay_cupo():
            return f"La materia {materia.nombre} no tiene cupos disponibles"

        nota = datos.get("nota", "")
        if nota not in ("", None) and not Materia.es_nota_valida(nota):
            return "La nota debe ser un número entre 0 y 20"
        return None

    def crear(self, datos):
        error = self.validar(datos)
        if error:
            return False, error
        estudiante_id = int(datos["estudiante_id"])
        materia = self.materias.obtener(int(datos["materia_id"]))
        matricula = Matricula(
            self.siguiente(),
            estudiante_id,
            materia.id,
            str(datos["periodo"]).strip(),
            datos.get("nota", ""),
        )
        materia.ocupar_cupo()
        self.materias.guardar()
        self.lista.append(matricula)
        self.guardar()
        return True, f"Matrícula {matricula.id} registrada"

    def actualizar(self, id_matricula, datos):
        return False, "Las matrículas no se modifican; registre la nota o retire la matrícula"

    def eliminar(self, id_matricula):
        return self.retirar_matricula(id_matricula)

    def registrar_nota(self, id_matricula, nota):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        if not Materia.es_nota_valida(nota):
            return False, "La nota debe ser un número entre 0 y 20"
        matricula.nota = float(nota)
        self.guardar()
        return True, f"Nota registrada: {matricula.nota:g} ({matricula.estado()})"

    def retirar_matricula(self, id_matricula):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return False, f"No existe la matrícula {id_matricula}"
        materia = self.materias.obtener(matricula.materia_id)
        if materia is not None:
            materia.liberar_cupo()
            self.materias.guardar()
        self.lista.remove(matricula)
        self.guardar()
        return True, f"Matrícula {id_matricula} retirada y cupo liberado"

    def certificado(self, id_matricula):
        matricula = self.obtener(id_matricula)
        if matricula is None:
            return None

        # Los índices por id resuelven cada referencia sin recorrer las listas.
        estudiantes = {e.id: e for e in self.estudiantes.leer()}
        materias = {m.id: m for m in self.materias.leer()}
        estudiante = estudiantes.get(matricula.estudiante_id)
        materia = materias.get(matricula.materia_id)

        nombre_estudiante = estudiante.nombre_completo() if estudiante else "eliminado"
        carnet = f" ({estudiante.carnet})" if estudiante else ""
        if materia:
            texto_materia = (f"{materia.nombre}   ({materia.codigo}) · "
                             f"{materia.creditos} créditos")
        else:
            texto_materia = "eliminada"
        nota = matricula.nota if matricula.nota != "" else "Pendiente"

        return (
            f"CERTIFICADO #{matricula.id}   periodo: {matricula.periodo}\n"
            f"Estudiante: {nombre_estudiante}{carnet}\n"
            f"Materia   : {texto_materia}\n"
            f"{'-' * 42}\n"
            f"Nota      : {nota}\n"
            f"Estado    : {matricula.estado()}"
        )

    def matriculas_por_estudiante(self):
        # El diccionario de listas agrupa matrículas usando estudiante_id como clave.
        agrupadas = {}
        for matricula in self.lista:
            agrupadas.setdefault(matricula.estudiante_id, []).append(matricula)
        return agrupadas

    def promedio_de_estudiante(self, id_estudiante):
        notas = [
            float(matricula.nota)
            for matricula in self.lista
            if matricula.estudiante_id == id_estudiante
            and Materia.es_nota_valida(matricula.nota)
        ]
        return round(sum(notas) / len(notas), 2) if notas else None

    def aprobadas(self):
        return [matricula for matricula in self.lista if matricula.esta_aprobada()]
