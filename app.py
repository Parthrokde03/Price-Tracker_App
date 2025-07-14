from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/track', methods=['POST'])
def track():
    url = request.form['url']

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'lxml')
    print(soup.prettify())

    image_url = soup.find('img',{'class':'DByuf4 IZexXJ jLEJ7H'})
    title = soup.find('span', {'class': 'VU-ZEz'})
    price = soup.find('div', {'class': 'Nx9bqj CxhGGd'})
    
    return render_template('result.html',image_url = image_url["src"] if image_url else "Not found", title=title.text.strip() if title else "Not found", price=price.text if price else "Not found")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
