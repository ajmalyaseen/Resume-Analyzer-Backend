from fastapi.middleware.cors import CORSMiddleware

# List of origins that are allowed to make requests to this API
# You can add your frontend URL here (e.g., ["http://localhost:3000"])
# ["*"] allows all origins, which is okay for development but should be restricted in production.
origins = ["*"]

def setup_cors(app):
    """
    Configures CORS middleware for the FastAPI application.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
        allow_headers=["*"],  # Allows all headers
    )
