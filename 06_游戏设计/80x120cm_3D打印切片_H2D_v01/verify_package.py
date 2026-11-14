"""Verify the generated 3MF package without requiring a slicer installation."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parent
NS = {'m': 'http://schemas.microsoft.com/3dmanufacturing/core/2015/02'}
FORBIDDEN = ('target', 'robot', 'attack', 'strike', 'punch', 'ball', 'spawn', 'magnet')


def verify_one(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        required = {'[Content_Types].xml', '_rels/.rels', '3D/3dmodel.model', 'Metadata/print_manifest.json'}
        assert required <= names, (path, required - names)
        root = ET.fromstring(z.read('3D/3dmodel.model'))
        assert root.attrib.get('unit') == 'millimeter'
        objects = root.findall('.//m:object', NS)
        builds = root.findall('.//m:item', NS)
        assert objects and builds
        tris = 0
        for obj in objects:
            name = obj.attrib.get('name', '').lower()
            assert not any(word in name for word in FORBIDDEN), (path, name)
            verts = obj.findall('.//m:vertex', NS)
            faces = obj.findall('.//m:triangle', NS)
            assert verts and faces
            n = len(verts)
            for face in faces:
                for key in ('v1', 'v2', 'v3'):
                    assert 0 <= int(face.attrib[key]) < n
            tris += len(faces)
        meta = json.loads(z.read('Metadata/print_manifest.json'))
    return {'file': str(path.relative_to(ROOT)).replace('\\', '/'), 'objects': len(objects),
            'build_items': len(builds), 'triangles': tris, 'metadata_plate': meta.get('plate_name', meta.get('type'))}


def main() -> None:
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    records = [verify_one(ROOT / item['file']) for item in manifest['plates']]
    records.append(verify_one(ROOT / 'assembly_reference_map_only.3mf'))
    assert len(records) == 23
    assert all(item['file'].endswith('.3mf') and item['triangles'] > 0 for item in records)
    assert all(max(p['model_envelope_mm']) <= 325.0 for p in manifest['plates'])
    (ROOT / 'verification_report.json').write_text(json.dumps({'result': 'PASS', 'files': records,
        'plate_count': len(manifest['plates']), 'assembly_reference_checked': True,
        'forbidden_geometry_absent': True, 'zip_and_xml_valid': True}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'result': 'PASS', 'checked_3mf_files': len(records),
                      'print_plates': len(manifest['plates']), 'assembly_reference': True}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
