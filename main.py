import os
from contextlib import asynccontextmanager
from html import escape
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse

from inventory import MAX_UPLOAD, initialize, list_items, review_csv, save_items


def table(items: list[tuple]) -> str:
    if not items:
        return "<p>No items.</p>"
    rows = "".join(
        f"<tr><td>{escape(sku)}</td><td>{escape(name)}</td><td>{quantity}</td></tr>"
        for sku, name, quantity in items
    )
    return (
        "<table><thead><tr><th>SKU</th><th>Name</th><th>Quantity</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
    )


def page(title: str, body: str, status: int = 200) -> HTMLResponse:
    return HTMLResponse(f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{title}</title><style>
body {{ font: 1rem system-ui; max-width: 48rem; margin: 3rem auto; padding: 0 1rem; }}
table {{ border-collapse: collapse; width: 100%; }}
td, th {{ padding: .5rem; text-align: left; border-bottom: 1px solid #bbb; }}
button {{ margin: .5rem 0; padding: .4rem .8rem; }}
</style></head><body><main><h1>{title}</h1>{body}</main></body></html>""", status)


def create_app(database: Path) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize(database)
        yield

    app = FastAPI(lifespan=lifespan)

    @app.get("/", response_class=HTMLResponse)
    def home():
        return page("Inventory CSV import", """
            <p>Upload a UTF-8 CSV with columns <code>sku,name,quantity</code>.</p>
            <form method="post" action="/preview" enctype="multipart/form-data">
              <label>CSV file <input type="file" name="file" accept=".csv,text/csv" required></label>
              <button>Review file</button>
            </form>
            <h2>Saved inventory</h2>
        """ + table(list_items(database)))

    @app.post("/preview", response_class=HTMLResponse)
    def preview(file: Annotated[UploadFile, File()]):
        try:
            data = file.file.read(MAX_UPLOAD + 1)
            if len(data) > MAX_UPLOAD:
                raise ValueError("The CSV must be 64 KiB or smaller.")
            source = data.decode("utf-8-sig")
            items, errors = review_csv(source)
        except UnicodeDecodeError:
            return page("Cannot read file", '<p>Save the CSV as UTF-8.</p><a href="/">Try again</a>', 400)
        except ValueError as error:
            return page("Cannot read file", f'<p>{escape(str(error))}</p><a href="/">Try again</a>', 400)

        issues = "".join(f"<li>{escape(error)}</li>" for error in errors)
        confirm = f"""
            <form method="post" action="/import">
              <textarea name="source" hidden>{escape(source)}</textarea>
              <button>Import valid rows</button>
            </form>
        """ if items else ""
        return page("Review import", f"""
            <p>{len(items)} valid, {len(errors)} invalid. Existing SKUs are skipped on import.</p>
            {table(items)}
            <ul>{issues}</ul>{confirm}<a href="/">Cancel</a>
        """)

    @app.post("/import", response_class=HTMLResponse)
    def confirm(source: Annotated[str, Form()]):
        try:
            items, errors = review_csv(source)
        except ValueError as error:
            return page("Cannot import", f'<p>{escape(str(error))}</p><a href="/">Try again</a>', 400)
        added = save_items(database, items)
        return page("Import complete", f"""
            <p>{added} inserted, {len(items) - added} already saved, {len(errors)} invalid.</p>
            <a href="/">View inventory</a>
        """)

    return app


app = create_app(Path(os.environ.get("INVENTORY_DB", "inventory.sqlite3")))
