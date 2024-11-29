

class base_livre:
  def __init__(self,ressource):
    """
        ressource désigne soit le nom de fichier (local) correspondant au livre,
        soit une URL pointant vers un livre.
    """
    raise NotImplementedError("à définir dans les sous-classes")

  def type(self):
    """ renvoie le type (EPUB, PDF, ou autre) du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def titre(self):
    """ renvoie le titre du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def auteur(self):
    """ renvoie l'auteur du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def langue(self):
    """ renvoie la langue du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def sujet(self):
    """ renvoie le sujet du livre """
    raise NotImplementedError("à définir dans les sous-classes")

  def date(self):
    """ renvoie la date de publication du livre """
    raise NotImplementedError("à définir dans les sous-classes")
  
class base_bibli:
  def __init__(self,path):
    """ path désigne le répertoire contenant les livres de cette bibliothèque """
    raise NotImplementedError("à définir dans les sous-classes")

  def ajouter(self,livre):
    """
      Ajoute le livre à la bibliothèque """
    raise NotImplementedError("à définir dans les sous-classes")

  def rapport_livres(self,format,fichier):
    """
        Génère un état des livres de la bibliothèque.
        Il contient la liste des livres,
        et pour chacun d'eux
        son titre, son auteur, son type (PDF ou EPUB), et le nom du fichier correspondant.

        format: format du rapport (PDF ou EPUB)
        fichier: nom du fichier généré
    """
    raise NotImplementedError("à définir dans les sous-classes")

  def rapport_auteurs(self,format,fichier):
    """
        Génère un état des auteurs des livres de la bibliothèque.
        Il contient pour chaque auteur
        le titre de ses livres en bibliothèque et le nom du fichier correspondant au livre.
        le type (PDF ou EPUB),
        et le nom du fichier correspondant.

        format: format du rapport (PDF ou EPUB)
        fichier: nom du fichier généré
    """
    raise NotImplementedError("à définir dans les sous-classes")