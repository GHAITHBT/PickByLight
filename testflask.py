from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Sample data
data = [
    {"id": 1, "name": "Material A", "status": "available"},
    {"id": 2, "name": "Material B", "status": "out_of_stock"},
]

@app.route('/')
def index():
    return render_template('index6.html')

@app.route('/materials', methods=['GET'])
def get_materials():
    return jsonify(data)

@app.route('/material/<int:material_id>', methods=['GET'])
def get_material(material_id):
    material = next((item for item in data if item["id"] == material_id), None)
    if material is None:
        return jsonify({"error": "Material not found"}), 404
    return jsonify(material)

@app.route('/material', methods=['POST'])
def add_material():
    if not request.json or 'name' not in request.json:
        return jsonify({"error": "Bad request"}), 400
    new_material = {
        "id": len(data) + 1,
        "name": request.json['name'],
        "status": request.json.get('status', 'available')
    }
    data.append(new_material)
    return jsonify(new_material), 201

@app.route('/material/<int:material_id>', methods=['DELETE'])
def delete_material(material_id):
    global data
    data = [item for item in data if item["id"] != material_id]
    return jsonify({"result": "Material deleted"}), 200

if __name__ == '__main__':
    app.run(debug=True)
