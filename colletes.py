# bin/env/phython
import requests
import re
import numpy
from bs4 import BeautifulSoup

# Etape 1 récuérer le html de la source
# Etape 2: récupérer tous les liens dans la source
# Etape 3: filter les liens pour n'avoir que des pdf (avec requests body)
# Etape 4: telecharger le contenu de tous les pdf avec write

def get_Html(source='https://infolivres.org/livres-gratuits-pdf/histoire/histoire-de-rome/'):
    reponse = requests.get(source) # ouverture et demande les documents html de la page
    if reponse.status_code==200: # verification de l'ouverture de l'url
        reponse.text # metre en format texte
        soup = BeautifulSoup ( reponse.content , "html.parser") # recupere le code html
        return soup
    else:
        return None
    

def get_lien_url(soup):
    stokURL=[]
    # recuper tous les liens ,les stoker dans un tableau
    for lien in soup.find_all('a',attrs={'href': re.compile("^https://")}):
       if ('.pdf' in lien.get('href', [])):
            stokURL= numpy.append (stokURL,lien.get('href'))
   
    return stokURL

def charger(url):
    lien=get_lien_url(get_Html(url))
   # télécharge le fichier
    response = requests.get(lien.get('href'))

    # sauvgarder le fichier
    pdf = open("pdf"+str(i)+".pdf", 'wb')
    pdf.write(response.content)
    pdf.close()
    print("File ", i, " downloaded")

    def charge_tout(source):
        soup=get_Html(source)
        if soup!=None:
           url=get_lien_pdf (soup)
           i=0
           while i in range(len(i)):
                try:
                   charger(url[i])
                   i+=1
                except AttributeError as e:
                    i+=1
               

        else:
            pass

def domaine_site(url):
      return re.search(r"w?[a-v|x-z][\w%\+-\.]+\.(org|fr|com|net)",url).group()


def parcourir(url,url_visiter,nmax):
        while url and len(url_visiter)< nmax:
            url=self.url[0]
            try:
              get_lien_url(url)
              return url_visiter.append(url)
            except AttributeError:
                print(f"nous ne peuvont pas scroler {url}")


# mini-programe teste
if __name__=="__main__":

    print("test")
 
 



