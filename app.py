from flask import Flask, render_template, request, redirect, url_for,jsonify
import numpy as np
import pickle

# Load data
popular_df = pickle.load(open('popular.pkl', 'rb'))
pt = pickle.load(open('pt.pkl', 'rb'))
books = pickle.load(open('books.pkl', 'rb'))
book_meta = pickle.load(open('book_metadata.pkl', 'rb'))
similarity_scores = pickle.load(open('similarity_scores.pkl', 'rb'))

app = Flask(__name__)

# Global listings list for marketplace
listings = [
    {
        "title": "Atomic Habits",
        "price": "₹250",
        "condition": "Like New",
        "image": "https://images-na.ssl-images-amazon.com/images/I/81bGKUa1e0L.jpg"
    },

]

@app.route('/')
def index():
    return render_template('index.html',
                           book_name=list(popular_df['Book-Title'].values),
                           author=list(popular_df['Book-Author'].values),
                           images=list(popular_df['Image-URL-M'].values),
                           votes=list(popular_df['num_ratings'].values),
                           ratings=list(popular_df['avg_rating'].values)
                           )

@app.route('/recommend')
def recommend_page():
    return render_template('recommend.html')

@app.route('/recommend_books', methods=['POST'])
def recommend_books():
    user_input = request.form.get('user_input')

    try:
        index = np.where(pt.index == user_input)[0][0]
    except IndexError:
        return render_template('recommend.html', data=[], error="Book not found. Please try another title.")

    similar_items = sorted(list(enumerate(similarity_scores[index])), key=lambda x: x[1], reverse=True)[1:5]

    data = []
    for i in similar_items:
        item = []
        temp_df = books[books['Book-Title'] == pt.index[i[0]]].drop_duplicates('Book-Title')
        item.extend(temp_df['Book-Title'].values)
        item.extend(temp_df['Book-Author'].values)
        item.extend(temp_df['Image-URL-M'].values)
        data.append(item)

    return render_template('recommend.html', data=data, book_titles=list(pt.index))

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    print(f"Message from {name} ({email}): {message}")
    return render_template('contact.html', success=True)

@app.route('/marketplace')
def marketplace():
    # ✅ Use the global listings list
    return render_template('marketplace.html', listings=listings)

@app.route('/sell', methods=['GET', 'POST'])
def sell():
    if request.method == 'POST':
        title = request.form.get('title')
        price = request.form.get('price')
        condition = request.form.get('condition')
        image = request.form.get('image')

        if title and price and condition and image:
            listings.append({
                "title": title,
                "price": price,
                "condition": condition,
                "image": image
            })
            return redirect(url_for('marketplace'))
        else:
            return render_template('sell.html', error="All fields are required.")

    return render_template('sell.html')

@app.route('/genre/<genre>')
def genre_books(genre):
    genre = genre.lower()
    genre_df = book_meta[book_meta['genre'].str.lower() == genre].drop_duplicates('Book-Title')

    # Use placeholder ratings if not available
    votes = [0] * len(genre_df)
    ratings = [0] * len(genre_df)

    return render_template('genre.html',
                           genre=genre.title(),
                           book_name=list(genre_df['Book-Title'].values),
                           author=list(genre_df['Book-Author'].values),
                           images=list(genre_df['Image-URL-M'].values),
                           votes=votes,
                           ratings=ratings)




book_data = [
    {"name": "Book A", "author": "Author A", "image": "url_to_image_A"},
    {"name": "Book B", "author": "Author B", "image": "url_to_image_B"},
    {"name": "Book C", "author": "Author C", "image": "url_to_image_C"},
]

wishlist=[]
@app.route('/wishlist', methods=['GET', 'POST'])
def wishlist_api():
    global wishlist
    if request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name')
        author = data.get('author')
        image = data.get('image')
        rating = data.get('rating', '')
        votes = data.get('votes', '')

        if not name:
            return jsonify({"status": "error", "message": "Missing book name"}), 400

        # create book dict
        book = {
            "name": name,
            "author": author or "Unknown",
            "image": image or "",
            "rating": rating,
            "votes": votes
        }

        # Prevent duplicates by name (case-insensitive)
        if not any(b.get('name', '').strip().lower() == name.strip().lower() for b in wishlist):
            wishlist.append(book)
            return jsonify({"status": "success", "wishlist_count": len(wishlist)})
        else:
            return jsonify({"status": "exists", "wishlist_count": len(wishlist)})

    # GET
    return jsonify({"wishlist": wishlist})

@app.route('/wishlist/view')
def wishlist_view():
    return render_template('wishlist.html', wishlist=wishlist)



if __name__ == '__main__':
    app.run(debug=True)