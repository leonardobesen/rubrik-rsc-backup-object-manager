# Example Object
class ProtectedObject():
    def __init__(self, id: str,
                 name: str, object_type: str,
                 sla_id: str = None, sla_name: str = None) -> None:
        self.id = id
        self.name = name
        self.search_term = None
        self.location = None
        self.object_type = object_type
        self.sla_id = sla_id
        self.sla_name = sla_name

    def __str__(self):
        return f"""\nObject(id={self.id}, 
        name={self.name}, 
        type={self.object_type})"""
