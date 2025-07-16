from flask import Flask, render_template, request
import requests, os, re
from bs4 import BeautifulSoup
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///prices.db'
db = SQLAlchemy(app)

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(300), nullable=False)
    title = db.Column(db.String(300))
    price = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

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

    try:
        response = requests.get(scraper_url, params=params)
        soup = BeautifulSoup(response.content, 'html.parser')
    except Exception as e:
        return f"Error: {e}"

    # Default values
    title_text = "Not found"
    price_text = "0"
    image_url = "https://via.placeholder.com/300?text=Image+Not+Found"

    # Flipkart
    if 'flipkart.com' in product_url:
        title = soup.find('meta', {'property': 'og:title'})
        image = soup.find('meta', {'property': 'og:image'})
        price = soup.find('div', {'class': 'Nx9bqj CxhGGd'})  # Subject to change

        title_text = title['content'] if title else title_text
        price_text = price.text.strip() if price else price_text
        image_url = image['content'] if image else image_url

    # Amazon
    elif 'amazon.in' in product_url or 'amzn.in' in product_url:
        title = soup.find('span', {'id': 'productTitle'})
        image = soup.find('img', {'id': 'landingImage'})
        price = soup.find('span', {'class': 'a-price-whole'})

        title_text = title.text.strip() if title else title_text
        price_text = price.text.strip() if price else price_text
        image_url = image['src'] if image else image_url

    else:
        title_text = "Unsupported website"
        price_text = "0"
        image_url = "https://via.placeholder.com/300?text=No+Image"

    cleaned_price = re.sub(r'[^\d.]', '', price_text)
    price_value = float(cleaned_price) if cleaned_price else 0.0

    if price_value > 0:
        record = PriceHistory(url=product_url, title=title_text, price=price_value)
        db.session.add(record)
        db.session.commit()

    history = PriceHistory.query.filter_by(url=product_url).order_by(PriceHistory.date.asc()).limit(7).all()

    # Convert to IST and format for chart.js
    from_zone = pytz.utc
    to_zone = pytz.timezone('Asia/Kolkata')

    date_labels = []
    price_data = []

    for item in history:
        ist_time = item.date.replace(tzinfo=from_zone).astimezone(to_zone)
        formatted_date = ist_time.strftime('%Y-%m-%d %H:%M')
        date_labels.append(formatted_date)
        price_data.append(item.price)

    return render_template(
        'result.html',
        title=title_text,
        price=price_text,
        image_url=image_url,
        history=history,
        date_labels=date_labels,
        price_data=price_data
    )

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
