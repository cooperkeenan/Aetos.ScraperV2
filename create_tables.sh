-- Listings table to track all scraped listings
CREATE TABLE listings (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL UNIQUE,
    title TEXT,
    price NUMERIC(10, 2),
    location TEXT,
    image_url TEXT,
    description TEXT,
    
    -- Matching info
    product_id INTEGER REFERENCES products(id),
    match_confidence NUMERIC(5, 2),
    
    -- Timestamps
    first_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_price NUMERIC(10, 2),
    price_changed_at TIMESTAMP,
    
    -- Metadata
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'sold', 'removed')),
    times_seen INTEGER DEFAULT 1,
    
    CONSTRAINT unique_listing_url UNIQUE (url)
);

-- Indexes for common queries
CREATE INDEX idx_listings_product_id ON listings(product_id);
CREATE INDEX idx_listings_first_seen ON listings(first_seen_at DESC);
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_price ON listings(price);

-- Track price history (optional but useful)
CREATE TABLE listing_price_history (
    id SERIAL PRIMARY KEY,
    listing_id INTEGER NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    price NUMERIC(10, 2) NOT NULL,
    recorded_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_price_history_listing ON listing_price_history(listing_id, recorded_at DESC);
