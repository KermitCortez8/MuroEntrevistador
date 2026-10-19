#!/usr/bin/env bash
set -euo pipefail

muro_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$muro_root"

if [[ ! -x .venv/bin/python ]]; then
    printf '%s\n' 'Primero crea el entorno: python -m venv .venv' 'Después instala: .venv/bin/pip install -r requirements.txt'
    exit 1
fi

printf '%s\n' 'Muro · http://localhost:8501' 'En Codespaces abre Ports → 8501 → Open in Browser.' 'El protocolo del puerto interno debe ser HTTP; la URL de Codespaces usa HTTPS.' ''
exec .venv/bin/python -m streamlit run app.py
