import requests
from bs4 import BeautifulSoup
import re
import numpy

class bibli_scrap:
    def __init__(self,url=[],profondeur=3,nbmax=100):
        self.url=url
        self.url_visiter=[]
        self.profondeur=profondeur
        self.nbmax=nbmax

    def get_Html(self,source):
      reponse = requests.get(source) # ouverture et demande les documents html de la page
      if reponse.status_code==200: # verification de l'ouverture de l'url
          reponse.text # metre en format texte
          soup = BeautifulSoup ( reponse.content , "html.parser") # recupere le code html
          return soup
      else:
          return None
      
    """je recuper le nom du domaine du site"""
    def domaine_site(self,url):
       return re.search(r"w?[a-v|x-z][\w%\+-\.]+\.(org|fr|com|net)",url).group()
      

    def get_lien_url(self,url):
      soup= self.get_Html(url)
      domaine= self.domaine_site(url)
       
      for lien in soup.find_all('a',attrs={'href': re.compile("^https://")}):
        if ((domaine and "pdf") in lien.get('href', [])) or((domaine and "epub") in lien.get('href', [])) :
              self.add_url(lien.get('href'))
      print(self.url)
            
    
    def add_url(self,lien):
         if lien not in self.url and lien not in self.url_visiter:
             self.url.append(lien)

    """je parcour le nombre maximal de lien pour les scroler"""
    def parcourir(self):
        while self.url and len(self.url_visiter)< self.profondeur:
            url=self.url[0]
            try:
              self.get_lien_url(url)
              self.url_visiter.append(url)
            except AttributeError:
                print(f"nous ne peuvont pas scroler {url}")

    """je telecharge les fichiers"""
    def telecharger(self):
      for i in self.url_visiter:
        # je recuper les attribues du livre
        nom_livrres=self.get_Html(i).find("p",class_="Libros_Titulo").text
        if "pdf" in i:
         attribue= ".pdf"
        else:
          attribue= ".epub" 

        # télécharge le fichier  
        response = requests.get(i.get('href'))
      
        # sauvgarder le fichier
        pdf = open(nom_livrres+str(i)+ attribue, 'wb')
        pdf.write(response.content)
        pdf.close()
        print("File ", i, " downloaded")
    
pass

bibli_scrap(['https://infolivres.org/livres-gratuits-pdf/histoire/histoire-de-rome/']).parcourir()