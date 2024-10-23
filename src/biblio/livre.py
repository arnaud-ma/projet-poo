class base_livre:
    def __init__(self, ressource):
        """
        ressource désigne soit le nom de fichier (local) correspondant au livre,
        soit une URL pointant vers un livre.
        """
        raise NotImplementedError("à définir dans les sous-classes")

    def type(self):
        """renvoie le type (EPUB, PDF, ou autre) du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    def titre(self):
        """renvoie le titre du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    def auteur(self):
        """renvoie l'auteur du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    def langue(self):
        """renvoie la langue du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    def sujet(self):
        """renvoie le sujet du livre"""
        raise NotImplementedError("à définir dans les sous-classes")

    def date(self):
        """renvoie la date de publication du livre"""
        raise NotImplementedError("à définir dans les sous-classes")
