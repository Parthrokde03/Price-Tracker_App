from flask import Flask, render_template, request
import requests, os, re
from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

# Flask app setup
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prices.db'
db = SQLAlchemy(app)

# Model for price history
class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(300), nullable=False)
    title = db.Column(db.String(300))
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# Home page
@app.route('/')
def index():
    return render_template('index.html')

# Product tracking route
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
    soup = BeautifulSoup(response.content, 'html.parser')

    # Flipkart
    if 'flipkart.com' in product_url:
        image = soup.find('meta', {'property': 'og:image'})
        title = soup.find('meta', {'property': 'og:title'})
        price = soup.find('div', {'class': 'Nx9bqj CxhGGd'})  # May change

        title_text = title['content'] if title else "Not found"
        price_text = price.text if price else "Not found"
        image_url = image['content'] if image else "https://via.placeholder.com/300?text=Image+Not+Found"

    # Amazon
    elif 'amazon' in product_url:
        image = soup.find('img', {'id': 'landingImage'})
        title = soup.find('span', {'id': 'productTitle'})
        price = soup.find('span', {'class': 'a-price-whole'})

        title_text = title.text.strip() if title else "Not found"
        price_text = price.text if price else "Not found"
        image_url = image['src'] if image else "https://via.placeholder.com/300?text=Image+Not+Found"

    else:
        title_text = "Unsupported website"
        price_text = "N/A"
        image_url = "https://via.placeholder.com/300?text=No+Image"

    # Clean price and store to DB
    cleaned_price = re.sub(r'[^\d.]', '', price_text)
    price_value = float(cleaned_price) if cleaned_price else 0.0

    if price_value > 0:
        record = PriceHistory(url=product_url, title=title_text, price=price_value)
        db.session.add(record)
        db.session.commit()

    # Fetch last 7 records
    history = PriceHistory.query.filter_by(url=product_url).order_by(PriceHistory.date.asc()).limit(7).all()

    # Convert each record’s datetime to IST formatted string
    from_zone = pytz.utc
    to_zone = pytz.timezone('Asia/Kolkata')
    for item in history:
        ist_time = item.date.replace(tzinfo=from_zone).astimezone(to_zone)
        item.date = ist_time.strftime('%d %b %Y %H:%M:%S IST')

    return render_template(
        'result.html',
        title=title_text,
        price=price_text,
        image_url=image_url,
        history=history
    )

# Run server
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
