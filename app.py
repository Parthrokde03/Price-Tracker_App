from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/track', methods=['POST'])
def track():
    product_url = request.form['url']

    scraper_url = 'http://api.scraperapi.com'
    api_key = '4131f2bc55e8754180a90cfb89d1d309'

    params = {
        'api_key': api_key,
        'url': product_url,
        'render': 'true'
    }

    response = requests.get(scraper_url, params=params)
    soup = BeautifulSoup(response.content, 'html.parser')  # Not lxml — use html.parser for meta tags

    # Fetch from meta tags
    image = soup.find('meta', {'property': 'og:image'})
    title = soup.find('meta', {'property': 'og:title'})
    price = soup.find('meta', {'property': 'product:price:amount'})

    return render_template(
        'result.html',
        title=title['content'] if title else "Not found",
        price=f"₹{price['content']}" if price else "Not found",
        image_url=image['content'] if image else "https://via.placeholder.com/300?text=Image+Not+Found"
    )


if __name__ == '__main__':
    app.run(debug=True)
