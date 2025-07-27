"""Integration tests for file upload and download functionality.

This module tests:
- File upload handling with multipart forms
- File download and static file serving
- File validation and security checks
- Error handling for file operations
- Form data parsing with files
- UploadFile integration
"""

import io
import tempfile
from pathlib import Path

from starlette.datastructures import UploadFile
from starlette.responses import FileResponse
from starlette.testclient import TestClient

from starhtml import star_app
from starhtml.server import JSONResponse
from starhtml.utils import form2dict, parse_form


class TestFileUpload:
    """Test file upload functionality."""

    def test_single_file_upload(self):
        """Test uploading a single file."""
        app, rt = star_app()

        @rt("/upload", methods=["POST"])
        async def upload_file(request):
            form_data = await request.form()
            uploaded_file = form_data.get("file")

            if not uploaded_file or not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            # Read file content
            content = await uploaded_file.read()

            return {
                "filename": uploaded_file.filename,
                "content_type": uploaded_file.content_type,
                "size": len(content),
                "content": content.decode() if content else "",
            }

        client = TestClient(app)

        # Create test file
        test_content = "Hello, World!"
        test_file = io.BytesIO(test_content.encode())

        response = client.post("/upload", files={"file": ("test.txt", test_file, "text/plain")})

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "test.txt"
        assert data["content_type"] == "text/plain"
        assert data["size"] == len(test_content)
        assert data["content"] == test_content

    def test_multiple_file_upload(self):
        """Test uploading multiple files."""
        app, rt = star_app()

        @rt("/upload-multiple", methods=["POST"])
        async def upload_multiple(request):
            form_data = await request.form()
            files = form_data.getlist("files")

            results = []
            for uploaded_file in files:
                if isinstance(uploaded_file, UploadFile):
                    content = await uploaded_file.read()
                    results.append(
                        {
                            "filename": uploaded_file.filename,
                            "size": len(content),
                            "content_type": uploaded_file.content_type,
                        }
                    )

            return {"uploaded_files": results, "count": len(results)}

        client = TestClient(app)

        # Create multiple test files
        files = [
            ("files", ("file1.txt", io.BytesIO(b"Content 1"), "text/plain")),
            ("files", ("file2.txt", io.BytesIO(b"Content 2"), "text/plain")),
            ("files", ("file3.json", io.BytesIO(b'{"key": "value"}'), "application/json")),
        ]

        response = client.post("/upload-multiple", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

        filenames = [f["filename"] for f in data["uploaded_files"]]
        assert "file1.txt" in filenames
        assert "file2.txt" in filenames
        assert "file3.json" in filenames

    def test_file_upload_with_form_data(self):
        """Test file upload combined with other form data."""
        app, rt = star_app()

        @rt("/upload-with-data", methods=["POST"])
        async def upload_with_data(request):
            form_data = await request.form()

            # Extract file
            uploaded_file = form_data.get("document")
            title = form_data.get("title", "")
            description = form_data.get("description", "")

            if not uploaded_file or not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            content = await uploaded_file.read()

            return {
                "file_info": {
                    "filename": uploaded_file.filename,
                    "size": len(content),
                    "content_type": uploaded_file.content_type,
                },
                "metadata": {"title": title, "description": description},
            }

        client = TestClient(app)

        # Test file with form data
        test_file = io.BytesIO(b"Document content")
        response = client.post(
            "/upload-with-data",
            files={"document": ("report.pdf", test_file, "application/pdf")},
            data={"title": "Annual Report", "description": "Company annual report for 2024"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["file_info"]["filename"] == "report.pdf"
        assert data["file_info"]["content_type"] == "application/pdf"
        assert data["metadata"]["title"] == "Annual Report"
        assert data["metadata"]["description"] == "Company annual report for 2024"

    def test_file_upload_type_validation(self):
        """Test file type validation."""
        app, rt = star_app()

        ALLOWED_TYPES = {"text/plain", "application/json", "image/jpeg", "image/png"}

        @rt("/upload-validated", methods=["POST"])
        async def upload_validated(request):
            form_data = await request.form()
            uploaded_file = form_data.get("file")

            if not uploaded_file or not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            if uploaded_file.content_type not in ALLOWED_TYPES:
                return JSONResponse(
                    {
                        "error": f"File type {uploaded_file.content_type} not allowed",
                        "allowed_types": list(ALLOWED_TYPES),
                    },
                    status_code=415,
                )

            content = await uploaded_file.read()
            return {"message": "File uploaded successfully", "filename": uploaded_file.filename, "size": len(content)}

        client = TestClient(app)

        # Test allowed file type
        response = client.post("/upload-validated", files={"file": ("test.txt", io.BytesIO(b"content"), "text/plain")})
        assert response.status_code == 200

        # Test disallowed file type
        response = client.post(
            "/upload-validated", files={"file": ("test.exe", io.BytesIO(b"content"), "application/x-executable")}
        )
        assert response.status_code == 415
        assert "not allowed" in response.json()["error"]

    def test_file_size_validation(self):
        """Test file size validation."""
        app, rt = star_app()

        MAX_SIZE = 1024  # 1KB limit

        @rt("/upload-size-check", methods=["POST"])
        async def upload_size_check(request):
            form_data = await request.form()
            uploaded_file = form_data.get("file")

            if not uploaded_file or not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            content = await uploaded_file.read()

            if len(content) > MAX_SIZE:
                return JSONResponse(
                    {"error": f"File too large. Maximum size: {MAX_SIZE} bytes", "actual_size": len(content)},
                    status_code=413,
                )

            return {"message": "File uploaded successfully", "filename": uploaded_file.filename, "size": len(content)}

        client = TestClient(app)

        # Test file within size limit
        small_content = b"x" * 500  # 500 bytes
        response = client.post(
            "/upload-size-check", files={"file": ("small.txt", io.BytesIO(small_content), "text/plain")}
        )
        assert response.status_code == 200

        # Test file exceeding size limit
        large_content = b"x" * 2000  # 2KB
        response = client.post(
            "/upload-size-check", files={"file": ("large.txt", io.BytesIO(large_content), "text/plain")}
        )
        assert response.status_code == 413
        assert "too large" in response.json()["error"]


class TestFileDownload:
    """Test file download functionality."""

    def test_file_download_response(self):
        """Test file download functionality."""
        app, rt = star_app()

        @rt("/download")
        def download_file(filename: str = "default.txt"):
            # Test file download with query parameter instead of path parameter
            content = f"Downloaded content for {filename}"

            # Import here to avoid circular imports
            from starlette.responses import Response

            response = Response(
                content=content,
                media_type="text/plain",
                headers={"Content-Disposition": f'attachment; filename="{filename}"'},
            )
            return response

        client = TestClient(app)

        response = client.get("/download?filename=test-file.txt")

        assert response.status_code == 200
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert "test-file.txt" in response.headers.get("content-disposition", "")
        assert "Downloaded content for test-file.txt" in response.text

    def test_static_file_serving(self):
        """Test static file serving functionality."""
        app, rt = star_app()

        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create test files with supported extensions
            (tmp_path / "style.css").write_text("body { color: blue; }")
            (tmp_path / "script.js").write_text("console.log('hello');")
            (tmp_path / "data.txt").write_text("plain text data")  # Use .txt instead of .json

            # Set up static file routing
            app.static_route_exts(static_path=str(tmp_path))

            client = TestClient(app)

            # Test CSS file
            response = client.get("/style.css")
            assert response.status_code == 200
            assert "body { color: blue; }" in response.text

            # Test JavaScript file
            response = client.get("/script.js")
            assert response.status_code == 200
            assert "console.log" in response.text

            # Test text file
            response = client.get("/data.txt")
            assert response.status_code == 200
            assert response.text == "plain text data"

    def test_file_not_found(self):
        """Test handling of missing files."""
        app, rt = star_app()

        @rt("/download-missing/{filename}")
        def download_missing(filename: str):
            nonexistent_path = f"/tmp/nonexistent/{filename}"
            return FileResponse(path=nonexistent_path, filename=filename)

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/download-missing/missing.txt")
        assert response.status_code == 404

    def test_download_with_custom_headers(self):
        """Test file download with custom headers."""
        app, rt = star_app()

        @rt("/download-custom/{filename}")
        def download_custom(filename: str):
            content = "Custom download content"

            from starlette.responses import Response

            response = Response(
                content=content,
                media_type="application/octet-stream",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "X-Custom-Header": "custom-value",
                    "Cache-Control": "no-cache",
                },
            )

            return response

        client = TestClient(app)

        response = client.get("/download-custom/custom.bin")

        assert response.status_code == 200
        assert response.headers["x-custom-header"] == "custom-value"
        assert response.headers["cache-control"] == "no-cache"
        assert response.headers["content-type"] == "application/octet-stream"
        assert "custom.bin" in response.headers.get("content-disposition", "")


class TestFormParsing:
    """Test form parsing functionality."""

    def test_parse_form_multipart(self):
        """Test parse_form with multipart data."""
        app, rt = star_app()

        @rt("/test-parse", methods=["POST"])
        async def test_parse(request):
            form_data = await parse_form(request)
            return {
                "type": type(form_data).__name__,
                "keys": list(form_data.keys()) if hasattr(form_data, "keys") else [],
                "text_field": form_data.get("text_field", ""),
                "has_file": "file_field" in form_data,
            }

        client = TestClient(app)

        response = client.post(
            "/test-parse",
            files={"file_field": ("test.txt", io.BytesIO(b"content"), "text/plain")},
            data={"text_field": "test value"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type"] == "FormData"
        assert "text_field" in data["keys"]
        assert "file_field" in data["keys"]
        assert data["text_field"] == "test value"
        assert data["has_file"] is True

    def test_parse_form_json(self):
        """Test parse_form with JSON data."""
        app, rt = star_app()

        @rt("/test-parse-json", methods=["POST"])
        async def test_parse_json(request):
            data = await parse_form(request)
            return {"type": type(data).__name__, "data": data}

        client = TestClient(app)

        test_data = {"key": "value", "number": 42}
        response = client.post("/test-parse-json", json=test_data)

        assert response.status_code == 200
        result = response.json()
        assert result["type"] in ["dict", "list"]  # JSON returns dict
        assert result["data"] == test_data

    def test_form2dict_conversion(self):
        """Test form2dict utility function."""
        app, rt = star_app()

        @rt("/test-form2dict", methods=["POST"])
        async def test_form2dict(request):
            form_data = await request.form()
            dict_data = form2dict(form_data)

            return {
                "original_type": type(form_data).__name__,
                "converted_type": type(dict_data).__name__,
                "data": dict_data,
            }

        client = TestClient(app)

        response = client.post(
            "/test-form2dict", data={"name": "John", "age": "30", "skills": ["python", "javascript"]}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["original_type"] == "FormData"
        assert result["converted_type"] == "dict"
        assert result["data"]["name"] == "John"
        assert result["data"]["age"] == "30"

    def test_empty_multipart_form(self):
        """Test handling of empty multipart forms."""
        app, rt = star_app()

        @rt("/test-empty-form", methods=["POST"])
        async def test_empty_form(request):
            form_data = await parse_form(request)
            return {
                "type": type(form_data).__name__,
                "empty": len(form_data) == 0,
                "keys": list(form_data.keys()) if hasattr(form_data, "keys") else [],
            }

        client = TestClient(app)

        # Send empty multipart form
        response = client.post(
            "/test-empty-form",
            files={},  # Empty files dict creates multipart form
            data={},  # Empty data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["type"] == "FormData"
        assert result["empty"] is True
        assert result["keys"] == []


class TestFileErrorHandling:
    """Test error handling in file operations."""

    def test_invalid_multipart_boundary(self):
        """Test handling of invalid multipart boundary."""
        app, rt = star_app()

        @rt("/test-invalid-boundary", methods=["POST"])
        async def test_invalid_boundary(request):
            try:
                form_data = await parse_form(request)
                return {"success": True, "type": type(form_data).__name__}
            except Exception as e:
                return JSONResponse({"error": str(e), "type": type(e).__name__}, status_code=400)

        client = TestClient(app)

        # Send malformed multipart data
        response = client.post(
            "/test-invalid-boundary",
            content="invalid multipart data",
            headers={"content-type": "multipart/form-data"},  # Missing boundary
        )

        assert response.status_code == 400
        data = response.json()
        assert "boundary" in data["error"].lower()

    def test_file_upload_without_file(self):
        """Test file upload endpoint when no file is provided."""
        app, rt = star_app()

        @rt("/upload-required", methods=["POST"])
        async def upload_required(request):
            form_data = await request.form()
            uploaded_file = form_data.get("required_file")

            if not uploaded_file:
                return JSONResponse({"error": "File is required"}, status_code=400)

            if not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "Invalid file format"}, status_code=400)

            return {"message": "File uploaded successfully"}

        client = TestClient(app)

        # Test with no file
        response = client.post("/upload-required", data={"other_field": "value"})
        assert response.status_code == 400
        assert "required" in response.json()["error"].lower()

        # Test with empty string instead of file
        response = client.post("/upload-required", data={"required_file": ""})
        assert response.status_code == 400

    def test_upload_file_read_error(self):
        """Test handling of file read errors."""
        app, rt = star_app()

        @rt("/upload-read-test", methods=["POST"])
        async def upload_read_test(request):
            form_data = await request.form()
            uploaded_file = form_data.get("file")

            if not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            try:
                content = await uploaded_file.read()
                # Attempt to read again (should work)
                await uploaded_file.seek(0)
                content2 = await uploaded_file.read()

                return {
                    "first_read_size": len(content),
                    "second_read_size": len(content2),
                    "reads_match": content == content2,
                }
            except Exception as e:
                return JSONResponse({"error": f"Read error: {str(e)}"}, status_code=500)

        client = TestClient(app)

        test_content = b"Test file content"
        response = client.post(
            "/upload-read-test", files={"file": ("test.txt", io.BytesIO(test_content), "text/plain")}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["first_read_size"] == len(test_content)
        assert data["second_read_size"] == len(test_content)
        assert data["reads_match"] is True


class TestFileSecurityAndValidation:
    """Test file security and validation scenarios."""

    def test_filename_sanitization(self):
        """Test handling of malicious filenames."""
        app, rt = star_app()

        @rt("/upload-filename-test", methods=["POST"])
        async def upload_filename_test(request):
            form_data = await request.form()
            uploaded_file = form_data.get("file")

            if not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            # Basic filename sanitization
            safe_filename = uploaded_file.filename
            if safe_filename:
                # Remove directory traversal attempts
                safe_filename = safe_filename.replace("..", "").replace("/", "").replace("\\", "")

                # Check for suspicious patterns
                suspicious_patterns = ["../", "..\\", "/etc/", "C:\\"]
                is_suspicious = any(pattern in (uploaded_file.filename or "") for pattern in suspicious_patterns)

                return {
                    "original_filename": uploaded_file.filename,
                    "safe_filename": safe_filename,
                    "is_suspicious": is_suspicious,
                    "size": len(await uploaded_file.read()),
                }

            return {"error": "No filename provided"}

        client = TestClient(app)

        # Test normal filename
        response = client.post(
            "/upload-filename-test", files={"file": ("normal.txt", io.BytesIO(b"content"), "text/plain")}
        )
        assert response.status_code == 200
        data = response.json()
        assert not data["is_suspicious"]
        assert data["safe_filename"] == "normal.txt"

        # Test malicious filename
        response = client.post(
            "/upload-filename-test", files={"file": ("../../../etc/passwd", io.BytesIO(b"content"), "text/plain")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_suspicious"] is True
        assert ".." not in data["safe_filename"]
        assert "/" not in data["safe_filename"]

    def test_file_content_validation(self):
        """Test validation of file content."""
        app, rt = star_app()

        @rt("/upload-content-check", methods=["POST"])
        async def upload_content_check(request):
            form_data = await request.form()
            uploaded_file = form_data.get("file")

            if not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            content = await uploaded_file.read()

            # Check for potentially malicious content
            dangerous_patterns = [b"<script", b"javascript:", b"<?php", b"#!/bin/"]
            has_dangerous_content = any(pattern in content.lower() for pattern in dangerous_patterns)

            # Basic file type validation by content
            is_text = True
            try:
                content.decode("utf-8")
            except UnicodeDecodeError:
                is_text = False

            return {
                "filename": uploaded_file.filename,
                "size": len(content),
                "is_text": is_text,
                "has_dangerous_content": has_dangerous_content,
                "first_bytes": content[:50].hex() if len(content) > 0 else "",
            }

        client = TestClient(app)

        # Test safe text file
        response = client.post(
            "/upload-content-check", files={"file": ("safe.txt", io.BytesIO(b"Hello, safe content!"), "text/plain")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["is_text"] is True
        assert data["has_dangerous_content"] is False

        # Test potentially dangerous content
        response = client.post(
            "/upload-content-check",
            files={"file": ("script.html", io.BytesIO(b"<script>alert('xss')</script>"), "text/html")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["has_dangerous_content"] is True


class TestRealWorldFileScenarios:
    """Test realistic file handling scenarios."""

    def test_image_upload_with_metadata(self):
        """Test image upload with metadata extraction."""
        app, rt = star_app()

        @rt("/upload-image", methods=["POST"])
        async def upload_image(request):
            form_data = await request.form()

            image_file = form_data.get("image")
            title = form_data.get("title", "")
            alt_text = form_data.get("alt_text", "")

            if not isinstance(image_file, UploadFile):
                return JSONResponse({"error": "No image uploaded"}, status_code=400)

            # Validate image type
            if not image_file.content_type.startswith("image/"):
                return JSONResponse({"error": "File must be an image"}, status_code=415)

            content = await image_file.read()

            return {
                "image_info": {
                    "filename": image_file.filename,
                    "content_type": image_file.content_type,
                    "size": len(content),
                },
                "metadata": {"title": title, "alt_text": alt_text},
                "upload_success": True,
            }

        client = TestClient(app)

        # Create fake image data (minimal PNG header)
        fake_png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50

        response = client.post(
            "/upload-image",
            files={"image": ("photo.png", io.BytesIO(fake_png), "image/png")},
            data={"title": "My Photo", "alt_text": "A beautiful landscape"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["upload_success"] is True
        assert data["image_info"]["content_type"] == "image/png"
        assert data["metadata"]["title"] == "My Photo"
        assert data["metadata"]["alt_text"] == "A beautiful landscape"

    def test_document_upload_with_processing(self):
        """Test document upload with basic processing."""
        app, rt = star_app()

        @rt("/upload-document", methods=["POST"])
        async def upload_document(request):
            form_data = await request.form()

            doc_file = form_data.get("document")
            category = form_data.get("category", "general")

            if not isinstance(doc_file, UploadFile):
                return JSONResponse({"error": "No document uploaded"}, status_code=400)

            content = await doc_file.read()

            # Basic document analysis
            is_text_doc = doc_file.content_type.startswith("text/")
            word_count = 0

            if is_text_doc:
                try:
                    text_content = content.decode("utf-8")
                    word_count = len(text_content.split())
                except UnicodeDecodeError:
                    is_text_doc = False

            return {
                "document_info": {
                    "filename": doc_file.filename,
                    "content_type": doc_file.content_type,
                    "size": len(content),
                    "category": category,
                },
                "analysis": {
                    "is_text_document": is_text_doc,
                    "word_count": word_count,
                    "estimated_read_time": max(1, word_count // 200),  # Rough estimate
                },
                "status": "processed",
            }

        client = TestClient(app)

        # Test text document
        doc_content = "This is a sample document with multiple words for testing purposes. " * 20
        response = client.post(
            "/upload-document",
            files={"document": ("report.txt", io.BytesIO(doc_content.encode()), "text/plain")},
            data={"category": "reports"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processed"
        assert data["document_info"]["category"] == "reports"
        assert data["analysis"]["is_text_document"] is True
        assert data["analysis"]["word_count"] > 0
        assert data["analysis"]["estimated_read_time"] > 0

    def test_bulk_file_upload(self):
        """Test bulk file upload scenario."""
        app, rt = star_app()

        @rt("/bulk-upload", methods=["POST"])
        async def bulk_upload(request):
            form_data = await request.form()

            # Get all uploaded files
            uploaded_files = []
            for key, value in form_data.multi_items():
                if isinstance(value, UploadFile):
                    content = await value.read()
                    uploaded_files.append(
                        {
                            "field_name": key,
                            "filename": value.filename,
                            "content_type": value.content_type,
                            "size": len(content),
                        }
                    )

            total_size = sum(f["size"] for f in uploaded_files)

            return {
                "files": uploaded_files,
                "summary": {
                    "total_files": len(uploaded_files),
                    "total_size": total_size,
                    "average_size": total_size // len(uploaded_files) if uploaded_files else 0,
                },
            }

        client = TestClient(app)

        # Upload multiple files with different field names
        files = [
            ("file1", ("doc1.txt", io.BytesIO(b"Content 1"), "text/plain")),
            ("file2", ("doc2.txt", io.BytesIO(b"Content 2 is longer"), "text/plain")),
            ("file3", ("data.json", io.BytesIO(b'{"key": "value"}'), "application/json")),
        ]

        response = client.post("/bulk-upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["summary"]["total_files"] == 3
        assert data["summary"]["total_size"] > 0

        filenames = [f["filename"] for f in data["files"]]
        assert "doc1.txt" in filenames
        assert "doc2.txt" in filenames
        assert "data.json" in filenames


class TestAdvancedFileHandlingScenarios:
    """Test advanced file handling scenarios and edge cases."""

    def test_multiple_files_same_name(self):
        """Test handling multiple files with the same form field name."""
        app, rt = star_app()

        @rt("/upload-multiple", methods=["POST"])
        async def upload_multiple_files(request):
            form_data = await request.form()

            # Get all files with the same name
            files = form_data.getlist("files[]")

            file_info = []
            for file in files:
                if isinstance(file, UploadFile):
                    content = await file.read()
                    file_info.append({"filename": file.filename, "size": len(content), "content": content.decode()})

            return {"uploaded_files": file_info, "count": len(file_info)}

        client = TestClient(app)

        # Upload multiple files with same field name
        files = [
            ("files[]", ("file1.txt", io.BytesIO(b"Content 1"), "text/plain")),
            ("files[]", ("file2.txt", io.BytesIO(b"Content 2"), "text/plain")),
            ("files[]", ("file3.txt", io.BytesIO(b"Content 3"), "text/plain")),
        ]

        response = client.post("/upload-multiple", files=files)
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 3
        assert len(data["uploaded_files"]) == 3
        assert data["uploaded_files"][0]["content"] == "Content 1"
        assert data["uploaded_files"][1]["content"] == "Content 2"
        assert data["uploaded_files"][2]["content"] == "Content 3"

    def test_empty_file_upload(self):
        """Test handling of empty file uploads."""
        app, rt = star_app()

        @rt("/upload-empty", methods=["POST"])
        async def upload_empty_file(request):
            form_data = await request.form()
            uploaded_file = form_data.get("file")

            if not uploaded_file or not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            content = await uploaded_file.read()

            return {"filename": uploaded_file.filename, "size": len(content), "is_empty": len(content) == 0}

        client = TestClient(app)

        # Upload empty file
        empty_file = ("file", ("empty.txt", io.BytesIO(b""), "text/plain"))
        response = client.post("/upload-empty", files=[empty_file])

        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "empty.txt"
        assert data["size"] == 0
        assert data["is_empty"] is True

    def test_file_upload_with_special_characters(self):
        """Test file upload with special characters in filename."""
        app, rt = star_app()

        @rt("/upload-special", methods=["POST"])
        async def upload_special_file(request):
            form_data = await request.form()
            uploaded_file = form_data.get("file")

            if not uploaded_file or not isinstance(uploaded_file, UploadFile):
                return JSONResponse({"error": "No file uploaded"}, status_code=400)

            # Check for potentially dangerous characters
            dangerous_chars = ["../", "\\", "<", ">", "|", ":", "*", "?", '"']
            has_dangerous = any(char in (uploaded_file.filename or "") for char in dangerous_chars)

            content = await uploaded_file.read()

            return {
                "original_filename": uploaded_file.filename,
                "has_dangerous_chars": has_dangerous,
                "size": len(content),
                "safe_filename": Path(uploaded_file.filename).name,  # Extract just the filename
            }

        client = TestClient(app)

        # Test various special character scenarios
        test_cases = [
            ("special chars.txt", False),
            ("file-with-dashes_and_underscores.txt", False),
            ("../../../etc/passwd", True),
            ("file<with>brackets.txt", True),
            ("file|with|pipes.txt", True),
            ("français.txt", False),  # Unicode should be OK
            ("file with spaces.txt", False),
        ]

        for filename, should_be_dangerous in test_cases:
            file_data = ("file", (filename, io.BytesIO(b"test content"), "text/plain"))
            response = client.post("/upload-special", files=[file_data])

            assert response.status_code == 200
            data = response.json()
            assert data["has_dangerous_chars"] == should_be_dangerous
            assert data["original_filename"] == filename
