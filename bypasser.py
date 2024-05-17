import re
import requests
from curl_cffi import requests as Nreq
import base64
from urllib.parse import unquote, urlparse, quote
import time
import cloudscraper
from bs4 import BeautifulSoup, NavigableString, Tag
from lxml import etree
import hashlib
import json
from asyncio import sleep as asleep
import ddl
from cfscrape import create_scraper
from json import load
from os import environ

with open('config.json', 'r') as f: DATA = load(f)
def getenv(var): return environ.get(var) or DATA.get(var, None)


##########################################################
# ENVs

GDTot_Crypt = getenv("CRYPT")
Laravel_Session = getenv("Laravel_Session")
XSRF_TOKEN = getenv("XSRF_TOKEN")
DCRYPT = getenv("DRIVEFIRE_CRYPT")
KCRYPT = getenv("KOLOP_CRYPT")
HCRYPT = getenv("HUBDRIVE_CRYPT")
KATCRYPT = getenv("KATDRIVE_CRYPT")
CF = getenv("CLOUDFLARE")

############################################################
# Lists

otherslist = ["exe.io","exey.io","sub2unlock.net","sub2unlock.com","rekonise.com","letsboost.net","ph.apps2app.com","mboost.me",
"sub4unlock.com","ytsubme.com","social-unlock.com","boost.ink","goo.gl","shrto.ml","t.co"]

gdlist = ["appdrive","driveapp","drivehub","gdflix","drivesharer","drivebit","drivelinks","driveace",
"drivepro","driveseed"]


###############################################################
# pdisk

def pdisk(url):
    r = requests.get(url).text
    try: return r.split("<!-- ")[-1].split(" -->")[0]
    except:
        try:return BeautifulSoup(r,"html.parser").find('video').find("source").get("src")
        except: return None

###############################################################
# index scrapper

def scrapeIndex(url, username="none", password="none"):

    def authorization_token(username, password):
        user_pass = f"{username}:{password}"
        return f"Basic {base64.b64encode(user_pass.encode()).decode()}"

          
    def decrypt(string): 
        return base64.b64decode(string[::-1][24:-20]).decode('utf-8')  

    
    def func(payload_input, url, username, password): 
        next_page = False
        next_page_token = "" 

        url = f"{url}/" if url[-1] != '/' else url

        try: headers = {"authorization":authorization_token(username,password)}
        except: return "username/password combination is wrong", None, None

        encrypted_response = requests.post(url, data=payload_input, headers=headers)
        if encrypted_response.status_code == 401: return "username/password combination is wrong", None, None

        try: decrypted_response = json.loads(decrypt(encrypted_response.text))
        except: return "something went wrong. check index link/username/password field again", None, None

        page_token = decrypted_response["nextPageToken"]
        if page_token is None: 
            next_page = False
        else: 
            next_page = True 
            next_page_token = page_token 


        if list(decrypted_response.get("data").keys())[0] != "error":
            file_length = len(decrypted_response["data"]["files"])
            result = ""

            for i, _ in enumerate(range(file_length)):
                files_type   = decrypted_response["data"]["files"][i]["mimeType"]
                if files_type != "application/vnd.google-apps.folder":
                        files_name   = decrypted_response["data"]["files"][i]["name"] 

                        direct_download_link = url + quote(files_name)
                        result += f"• {files_name} :\n{direct_download_link}\n\n"
            return result, next_page, next_page_token

    def format(result):
        long_string = ''.join(result)
        new_list = []

        while len(long_string) > 0:
            if len(long_string) > 4000:
                split_index = long_string.rfind("\n\n", 0, 4000)
                if split_index == -1:
                    split_index = 4000
            else:
                split_index = len(long_string)
                
            new_list.append(long_string[:split_index])
            long_string = long_string[split_index:].lstrip("\n\n")
        
        return new_list

    # main
    x = 0
    next_page = False
    next_page_token = "" 
    result = []

    payload = {"page_token":next_page_token, "page_index": x}	
    print(f"Index Link: {url}\n")
    temp, next_page, next_page_token = func(payload, url, username, password)
    if temp is not None: result.append(temp)
    
    while next_page == True:
        payload = {"page_token":next_page_token, "page_index": x}
        temp, next_page, next_page_token = func(payload, url, username, password)
        if temp is not None: result.append(temp)
        x += 1
        
    if len(result)==0: return None
    return format(result)

################################################################
# Shortner Full Page API

def shortner_fpage_api(link):
    link_pattern = r"https?://[\w.-]+/full\?api=([^&]+)&url=([^&]+)(?:&type=(\d+))?"
    match = re.match(link_pattern, link)
    if match:
        try:
            url_enc_value = match.group(2)
            url_value = base64.b64decode(url_enc_value).decode("utf-8")
            return url_value
        except BaseException:
            return None
    else:
        return None

# Shortner Quick Link API

def shortner_quick_api(link):
    link_pattern = r"https?://[\w.-]+/st\?api=([^&]+)&url=([^&]+)"
    match = re.match(link_pattern, link)
    if match:
        try:
            url_value = match.group(2)
            return url_value
        except BaseException:
            return None
    else:
        return None

##############################################################
# tnlink

def tnlink(url):
    client = requests.session()
    DOMAIN = "https://page.tnlink.in/"
    url = url[:-1] if url[-1] == '/' else url
    code = url.split("/")[-1]
    final_url = f"{DOMAIN}/{code}"
    ref = "https://usanewstoday.club/"
    h = {"referer": ref}
    while len(client.cookies) == 0:
        resp = client.get(final_url,headers=h)
        time.sleep(2)
    soup = BeautifulSoup(resp.content, "html.parser")
    inputs = soup.find_all("input")
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(8)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try: return r.json()['url']
    except: return "Something went wrong :("


###############################################################
# psa 

def try2link_bypass(url):
	client = cloudscraper.create_scraper(allow_brotli=False)
	
	url = url[:-1] if url[-1] == '/' else url
	
	params = (('d', int(time.time()) + (60 * 4)),)
	r = client.get(url, params=params, headers= {'Referer': 'https://newforex.online/'})
	
	soup = BeautifulSoup(r.text, 'html.parser')
	inputs = soup.find(id="go-link").find_all(name="input")
	data = { input.get('name'): input.get('value') for input in inputs }	
	time.sleep(7)
	
	headers = {'Host': 'try2link.com', 'X-Requested-With': 'XMLHttpRequest', 'Origin': 'https://try2link.com', 'Referer': url}
	
	bypassed_url = client.post('https://try2link.com/links/go', headers=headers,data=data)
	return bypassed_url.json()["url"]
		

def try2link_scrape(url):
	client = cloudscraper.create_scraper(allow_brotli=False)	
	h = {
	'upgrade-insecure-requests': '1', 'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36',
	}
	res = client.get(url, cookies={}, headers=h)
	url = 'https://try2link.com/'+re.findall('try2link\.com\/(.*?) ', res.text)[0]
	return try2link_bypass(url)
    

def psa_bypasser(psa_url):
    cookies = {'cf_clearance': CF }
    headers = {
        'authority': 'psa.wf',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'referer': 'https://psa.wf/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    r = requests.get(psa_url, headers=headers, cookies=cookies)
    soup = BeautifulSoup(r.text, "html.parser").find_all(class_="dropshadowboxes-drop-shadow dropshadowboxes-rounded-corners dropshadowboxes-inside-and-outside-shadow dropshadowboxes-lifted-both dropshadowboxes-effect-default")
    links = []
    for link in soup:
        try:
            exit_gate = link.a.get("href")
            if "/exit" in exit_gate:
                print("scraping :",exit_gate)
                links.append(try2link_scrape(exit_gate))
        except: pass

    finals = ""
    for li in links:
        try:
            res = requests.get(li, headers=headers, cookies=cookies)
            soup = BeautifulSoup(res.text,"html.parser")
            name = soup.find("h1",class_="entry-title", itemprop="headline").getText()
            finals += "**" + name + "**\n\n"
            soup = soup.find("div", class_="entry-content" ,itemprop="text").findAll("a")
            for ele in soup: finals += "○ " + ele.get("href") + "\n"
            finals += "\n\n"
        except: finals += li + "\n\n"
    return finals


##################################################################################################################
# rocklinks

def rocklinks(url):
    client = cloudscraper.create_scraper(allow_brotli=False)
    if 'rocklinks.net' in url:
        DOMAIN = "https://blog.disheye.com"
    else:
        DOMAIN = "https://rocklinks.net"

    url = url[:-1] if url[-1] == '/' else url

    code = url.split("/")[-1]
    if 'rocklinks.net' in url:
        final_url = f"{DOMAIN}/{code}?quelle=" 
    else:
        final_url = f"{DOMAIN}/{code}"

    resp = client.get(final_url)
    soup = BeautifulSoup(resp.content, "html.parser")
    
    try: inputs = soup.find(id="go-link").find_all(name="input")
    except: return "Incorrect Link"
    
    data = { input.get('name'): input.get('value') for input in inputs }

    h = { "x-requested-with": "XMLHttpRequest" }
    
    time.sleep(10)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()['url']
    except: return "Something went wrong :("


################################################
# igg games

def decodeKey(encoded):
        key = ''

        i = len(encoded) // 2 - 5
        while i >= 0:
            key += encoded[i]
            i = i - 2
        
        i = len(encoded) // 2 + 4
        while i < len(encoded):
            key += encoded[i]
            i = i + 2

        return key

def bypassBluemediafiles(url, torrent=False):
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Alt-Used': 'bluemediafiles.com',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    script = str(soup.findAll('script')[3])
    encodedKey = script.split('Create_Button("')[1].split('");')[0]

    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:103.0) Gecko/20100101 Firefox/103.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Referer': url,
        'Alt-Used': 'bluemediafiles.com',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
    }

    params = { 'url': decodeKey(encodedKey) }
    
    if torrent:
        res = requests.get('https://dl.pcgamestorrents.org/get-url.php', params=params, headers=headers)
        soup = BeautifulSoup(res.text,"html.parser")
        furl = soup.find("a",class_="button").get("href")

    else:
        res = requests.get('https://bluemediafiles.com/get-url.php', params=params, headers=headers)
        furl = res.url
        if "mega.nz" in furl:
            furl = furl.replace("mega.nz/%23!","mega.nz/file/").replace("!","#")

    return furl

def igggames(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.text,"html.parser")
    soup = soup.find("div",class_="uk-margin-medium-top").findAll("a")

    bluelist = []
    for ele in soup: bluelist.append(ele.get('href'))
    bluelist = bluelist[3:-1]

    links = ""
    last  = None
    fix = True
    for ele in bluelist:
        if ele == "https://igg-games.com/how-to-install-a-pc-game-and-update.html": 
            fix = False
            links += "\n"
        if "bluemediafile" in ele:
            tmp = bypassBluemediafiles(ele)
            if fix:
                tt = tmp.split("/")[2]
                if last is not None and tt != last: links += "\n"
                last = tt
            links = links + "○ " + tmp + "\n"
        elif "pcgamestorrents.com" in ele:
            res = requests.get(ele)
            soup = BeautifulSoup(res.text,"html.parser")
            turl = soup.find("p",class_="uk-card uk-card-body uk-card-default uk-card-hover").find("a").get("href")
            links = links + "🧲 `" + bypassBluemediafiles(turl,True) + "`\n\n"
        elif ele != "https://igg-games.com/how-to-install-a-pc-game-and-update.html":
            if fix:
                tt = ele.split("/")[2]
                if last is not None and tt != last: links += "\n"
                last = tt
            links = links + "○ " + ele + "\n"
       
    return links[:-1]


###############################################################
# htpmovies cinevood sharespark atishmkv

def htpmovies(link):
    client = cloudscraper.create_scraper(allow_brotli=False)
    r = client.get(link, allow_redirects=True).text
    j = r.split('("')[-1]
    url = j.split('")')[0]
    param = url.split("/")[-1]
    DOMAIN = "https://go.theforyou.in"
    final_url = f"{DOMAIN}/{param}"
    resp = client.get(final_url)
    soup = BeautifulSoup(resp.content, "html.parser")    
    try: inputs = soup.find(id="go-link").find_all(name="input")
    except: return "Incorrect Link"
    data = { input.get('name'): input.get('value') for input in inputs }
    h = { "x-requested-with": "XMLHttpRequest" }
    time.sleep(10)
    r = client.post(f"{DOMAIN}/links/go", data=data, headers=h)
    try:
        return r.json()['url']
    except: return "Something went Wrong !!"


def scrappers(link):
 
    try: link = re.match(r"((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*", link)[0]
    except TypeError: return 'Not a Valid Link.'
    links = []

    if "sharespark" in link:
        gd_txt = ""
        res = requests.get("?action=printpage;".join(link.split('?')))
        soup = BeautifulSoup(res.text, 'html.parser')
        for br in soup.findAll('br'):
            next_s = br.nextSibling
            if not (next_s and isinstance(next_s,NavigableString)):
                continue
            next2_s = next_s.nextSibling
            if next2_s and isinstance(next2_s,Tag) and next2_s.name == 'br':
              text = str(next_s).strip()
              if text:
                  result = re.sub(r'(?m)^\(https://i.*', '', next_s)
                  star = re.sub(r'(?m)^\*.*', ' ', result)
                  extra = re.sub(r'(?m)^\(https://e.*', ' ', star)
                  gd_txt += ', '.join(re.findall(r'(?m)^.*https://new1.gdtot.cfd/file/[0-9][^.]*', next_s)) + "\n\n"
        return gd_txt
  
    elif "htpmovies" in link and "/exit.php" in link:
        return htpmovies(link)
        
    elif "htpmovies" in link:
        prsd = ""
        links = []
        res = requests.get(link)
        soup = BeautifulSoup(res.text, 'html.parser')
        x = soup.select('a[href^="/exit.php?url="]')
        y = soup.select('h5')
        z = unquote(link.split('/')[-2]).split('-')[0] if link.endswith('/') else unquote(link.split('/')[-1]).split('-')[0]

        for a in x:
            links.append(a['href'])
            prsd = f"Total Links Found : {len(links)}\n\n"
      
        msdcnt = -1
        for b in y:
            if str(b.string).lower().startswith(z.lower()):
                msdcnt += 1
                url = f"https://htpmovies.lol"+links[msdcnt]
                prsd += f"{msdcnt+1}. <b>{b.string}</b>\n{htpmovies(url)}\n\n"
                asleep(5)
        return prsd

    elif "cinevood" in link:
        prsd = ""
        links = []
        res = requests.get(link)
        soup = BeautifulSoup(res.text, 'html.parser')
        x = soup.select('a[href^="https://kolop.icu/file"]')
        for a in x:
            links.append(a['href'])
        for o in links:
            res = requests.get(o)
            soup = BeautifulSoup(res.content, "html.parser")
            title = soup.title.string
            reftxt = re.sub(r'Kolop \| ', '', title)
            prsd += f'{reftxt}\n{o}\n\n'
        return prsd

    elif "atishmkv" in link:
        prsd = ""
        links = []
        res = requests.get(link)
        soup = BeautifulSoup(res.text, 'html.parser')
        x = soup.select('a[href^="https://gdflix.top/file"]')
        for a in x:
            links.append(a['href'])
        for o in links:
            prsd += o + '\n\n'
        return prsd

    elif "teluguflix" in link:
        gd_txt = ""
        r = requests.get(link)
        soup = BeautifulSoup (r.text, "html.parser")
        links = soup.select('a[href*="gdtot"]')
        gd_txt = f"Total Links Found : {len(links)}\n\n"
        for no, link in enumerate(links, start=1):
            gdlk = link['href']
            t = requests.get(gdlk)
            soupt = BeautifulSoup(t.text, "html.parser")
            title = soupt.select('meta[property^="og:description"]')
            gd_txt += f"{no}. <code>{(title[0]['content']).replace('Download ' , '')}</code>\n{gdlk}\n\n"
            asleep(1.5)
        return gd_txt
    
    elif "taemovies" in link:
        gd_txt, no = "", 0
        r = requests.get(link)
        soup = BeautifulSoup (r.text, "html.parser")
        links = soup.select('a[href*="shortingly"]')
        gd_txt = f"Total Links Found : {len(links)}\n\n"
        for a in links:
            glink = rocklinks(a["href"]) 
            t = requests.get(glink)
            soupt = BeautifulSoup(t.text, "html.parser")
            title = soupt.select('meta[property^="og:description"]')
            no += 1
            gd_txt += f"{no}. {(title[0]['content']).replace('Download ' , '')}\n{glink}\n\n"
        return gd_txt
    
    elif "toonworld4all" in link:
        gd_txt, no = "", 0
        r = requests.get(link)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.select('a[href*="redirect/main.php?"]')
        for a in links:
            down = requests.get(a['href'], stream=True, allow_redirects=False)
            link = down.headers["location"]
            glink = rocklinks(link)
            if glink and "gdtot" in glink:
                t = requests.get(glink)
                soupt = BeautifulSoup(t.text, "html.parser")
                title = soupt.select('meta[property^="og:description"]')
                no += 1
                gd_txt += f"{no}. {(title[0]['content']).replace('Download ' , '')}\n{glink}\n\n"
        return gd_txt
    
    elif "animeremux" in link:
        gd_txt, no = "", 0
        r = requests.get(link)
        soup = BeautifulSoup (r.text, "html.parser")
        links = soup.select('a[href*="urlshortx.com"]')
        gd_txt = f"Total Links Found : {len(links)}\n\n"
        for a in links:
            link = a["href"]
            x = link.split("url=")[-1]
       
