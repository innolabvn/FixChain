// MongoDB initialization script for FixChain

// Switch to the fixchain database
db = db.getSiblingDB('fixchain');

// Create the fix_thoughts_vector collection
db.createCollection('fix_thoughts_vector');

// Create a vector search index for the collection
// Note: In MongoDB 7.0+, vector search indexes are created differently
// This is a placeholder - actual vector index creation may need to be done via MongoDB Compass or Atlas CLI
try {
    db.fix_thoughts_vector.createIndex(
        { "embedding": "2dsphere" },
        { name: "vector_index" }
    );
    print("Vector index created successfully");
} catch (e) {
    print("Vector index creation failed (this is expected in local MongoDB): " + e.message);
    print("Vector search functionality may be limited without Atlas Vector Search");
}

// Create a text index for fallback search
db.fix_thoughts_vector.createIndex(
    { "text": "text", "metadata.bug_id": 1, "metadata.method_name": 1 },
    { name: "text_search_index" }
);

// Insert a sample document
db.fix_thoughts_vector.insertOne({
    text: "Sample bug fix reasoning for testing purposes",
    metadata: {
        bug_id: "SAMPLE-001",
        method_name: "testMethod",
        fix_type: "sample_fix",
        timestamp: new Date().toISOString(),
        severity: "low"
    },
    created_at: new Date()
});

print("FixChain database initialized successfully");