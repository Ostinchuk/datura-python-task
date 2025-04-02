import os

import uvicorn
from fastapi import FastAPI

app = FastAPI()

UVICORN_RELOAD = os.environ.get("UVICORN_RELOAD", "").upper() == "TRUE"


@app.get("/")
def read_root() -> dict[str, str]:
    return {"Hello": "World"}


def main():
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        workers=2,
        reload=UVICORN_RELOAD,
    )


if __name__ == "__main__":
    main()
