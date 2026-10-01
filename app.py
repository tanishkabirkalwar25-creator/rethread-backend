# Python AI service. Requires: tensorflow, flask, pillow, pytesseract (+ tesseract binary), numpy.
# Needs YOUR fabric-trained weights in MODEL_DIR: resnet50_fabric.keras, nasnet_fabric.keras, classes.json
# (ImageNet weights alone cannot identify fabrics). Without them, /analyze returns 503 -- it never invents results.
import base64, io, json, os
from flask import Flask, request, jsonify
from label import parse_composition
app = Flask(__name__); MD = os.environ.get("MODEL_DIR", "models"); M = {}
def load():
    if M: return True
    try:
        import tensorflow as tf
        M["classes"] = json.load(open(f"{MD}/classes.json"))
        M["r"] = tf.keras.models.load_model(f"{MD}/resnet50_fabric.keras"); M["n"] = tf.keras.models.load_model(f"{MD}/nasnet_fabric.keras")
        return True
    except Exception as e: app.logger.error("model load: %s", e); return False
def img(d):
    from PIL import Image; return Image.open(io.BytesIO(base64.b64decode(d.split(",", 1)[1]))).convert("RGB")
def predict(model, pre, im, size):
    import numpy as np
    x = pre(np.expand_dims(np.array(im.resize(size), dtype="float32"), 0)); p = model.predict(x, verbose=0)[0]; return p
@app.get("/health")
def health(): return jsonify(ok=True, models=bool(M) or os.path.exists(f"{MD}/classes.json"))
@app.post("/analyze")
def analyze():
    if not load(): return jsonify(error="models_unavailable"), 503
    import numpy as np
    from tensorflow.keras.applications.resnet50 import preprocess_input as pr
    from tensorflow.keras.applications.nasnet import preprocess_input as pn
    im = request.json["images"]; cls = M["classes"]
    src = im.get("fabric") or im["full"]   # close-up is stronger evidence when present
    a = img(src); pr_, pn_ = predict(M["r"], pr, a, (224, 224)), predict(M["n"], pn, a, (224, 224))
    avg = (pr_ + pn_) / 2; top = np.argsort(avg)[::-1][:3]
    ri, ni = int(pr_.argmax()), int(pn_.argmax()); agree = "HIGH" if ri == ni else "LOW"
    conf = float(avg[top[0]]); lvl = "HIGH" if conf >= .8 and agree == "HIGH" else "MEDIUM" if conf >= .55 else "LOW"
    final = cls[int(top[0])]
    comp = {"verified": False, "fibers": []}; label = False
    if im.get("label"):
        try:
            import pytesseract; f = parse_composition(pytesseract.image_to_string(img(im["label"]))); label = bool(f)
            comp = {"verified": bool(f), "fibers": f}
        except Exception as e: app.logger.error("ocr: %s", e)
    return jsonify(imageQuality="Medium", labelDetected=label, garment={"type": "Unknown", "level": "Unknown", "fullGarmentVisible": False, "reason": "Garment type is confirmed by you."},
        fabric={"primary": final, "level": lvl.capitalize(), "alternatives": [], "source": "ai_models"}, composition=comp, color={"primary": "Unknown"}, evidence=["Fabric close-up" if im.get("fabric") else "Full garment photo"], warnings=[],
        fabricAI={"finalPrediction": final, "confidence": conf, "confidenceLevel": lvl, "agreement": agree, "message": None if lvl != "LOW" else "We couldn't identify the fabric confidently. Try uploading a clear fabric close-up.",
                  "resnet50": {"prediction": cls[ri], "confidence": float(pr_[ri])}, "nasnet": {"prediction": cls[ni], "confidence": float(pn_[ni])},
                  "topPredictions": [{"fabric": cls[int(i)], "confidence": float(avg[i])} for i in top]})
