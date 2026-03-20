from conn import model,index

def search_products(user_query, min_price=None, max_price=None):
    # 1. Turn user text into a vector
    query_vector = model.encode(user_query).tolist()
    
    # 2. Build metadata filters (Optional)
    # This allows users to say "Cheap carrots" and we filter by price
    metadata_filter = {}

    # 3. Query Pinecone
    results = index.query(
        vector=query_vector,
        top_k=5,
        filter=metadata_filter if metadata_filter else None,
        include_metadata=True
    )
    
    return results['matches']


matches = search_products("coffee drink", max_price=500)

print(matches)