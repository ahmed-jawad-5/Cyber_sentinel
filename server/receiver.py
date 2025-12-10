def handle_conn(conn, addr, model_runner):
    try:
        data = b""

        while True:
            chunk = conn.recv(4096)
            if not chunk:
                break
            data += chunk
            if b"\n" in chunk:
                break

        text = data.decode().strip()
        if not text:
            return

        print("\n==================== RECEIVER DEBUG ====================")
        print(f"[DEBUG] Raw packet from {addr}: {text}")

        obj = json.loads(text)

        print("[DEBUG] Parsed JSON keys:", list(obj.keys()))

        ordered = validate_and_fill(obj)

        print("[DEBUG] Ordered feature dict (correct order):")
        print(ordered)
        print("[DEBUG] Feature vector (values only):")
        print(list(ordered.values()))
        print("========================================================")

        # Save row first:
        row_index = save_features_only(ordered)

        # Predict
        result = model_runner.predict(list(ordered.values()))

        print(
            f"[{addr}] {result['label'].upper()} "
            f"(error={result['reconstruction_error']:.6f})"
        )

        # Update CSV
        update_prediction(row_index,
                          result["reconstruction_error"],
                          result["label"])

    except Exception as e:
        print("Error handling connection:", e)

    finally:
        conn.close()
