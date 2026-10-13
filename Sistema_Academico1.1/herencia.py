# =====================================================================
# CLASE BASE: lo que los tres modelos comparten
# =====================================================================



class ModeloBase:
    """Padre de todos los modelos. Guarda el id y define el comportamiento común."""

    def __init__(self, id_registro):
        self.id = int(id_registro)
        self.name=self.__class__.__name__

    # ---- ÚNICO MÉTODO DE CLASE DEL PROYECTO ----
    @classmethod
    def desde_diccionario(cls, datos):
        """Diccionario -> objeto. Escrito UNA vez y usado por los tres modelos.
        cls es la clase que llamó: Cliente, Producto o Venta."""
        datos = dict(datos)                 # copia, para no tocar el original
        id_registro = datos.pop("id")       # saco el id
        return cls(id_registro)    # el resto son los campos del modelo

    # ---- MÉTODOS DE INSTANCIA ----
    def a_diccionario(self):
        # Objeto -> diccionario. Cada hijo agrega sus campos.
        return {"id": self.id,"name": self.name}

    def etiqueta(self):
        # POLIMORFISMO: cada hijo la reescribe a su manera
        return f"registro {self.id}"

    def __str__(self):
        # Lo que se ve al hacer print(objeto). Llama a etiqueta(),
        # así que cada modelo se imprime distinto sin cambiar esta línea.
        return f"[{self.id} {self.name}] {self.etiqueta()}"

mod1 = ModeloBase(1)
mod2 = ModeloBase.desde_diccionario({"id": 2,"name":"ModeloBase"}) # crea un objeto ModeloBase con id=2
print(mod1) # llama a __str__() que llama a etiqueta() que devuelve "registro 1"
print(mod1.id,mod1.name) # llama a id y name que devuelve 1 y ModeloBase
print(mod1.etiqueta()) # llama a etiqueta() que devuelve "registro 1"
print(mod1.a_diccionario()) # llama a a_diccionario() que devuelve {'id': 1, 'name': 'ModeloBase'}