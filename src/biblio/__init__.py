from biblio.bibli import base_bibli, simple_bibli
from biblio.livre import Epub, Livre, Pdf
from biblio.scrap import bibli, bibli_scrap

FORMATS_DISPONIBLES = set(Livre.SUFFIXES.keys())
__all__ = ["Epub", "Livre", "Pdf", "base_bibli", "bibli", "bibli_scrap", "simple_bibli"]
