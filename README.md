# Smart Wake-Up System: Proyecto Final de Visión por Ordenador

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![Status](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow)

> [cite_start]**Institución:** Universidad Pontificia Comillas (ICAI) - Ingeniería Matemática [cite: 1, 6]
> [cite_start]**Asignatura:** Visión por Ordenador I [cite: 3]
> **Curso:** 2025/2026

## 📖 Descripción del Proyecto

Este proyecto consiste en un sistema de visión artificial diseñado para funcionar como un **despertador inteligente**. El sistema monitoriza a un usuario durmiendo y garantiza que la alarma no se desactive hasta que se detecte efectivamente que el usuario se ha despertado y está activo.

[cite_start]El sistema integra módulos obligatorios de seguridad (decodificación de patrones visuales) y un módulo de aplicación libre (seguimiento del usuario al despertar)[cite: 32, 33].

### 🎯 Objetivo
Implementar un sistema robusto que:
1.  **Valide la identidad/acceso** mediante patrones visuales (Módulo de Seguridad).
2.  **Detecte y siga** al usuario (Tracker) para confirmar que está despierto.
3.  [cite_start]Funcione en **tiempo real** con una tasa de refresco adecuada[cite: 65].

---

## ⚙️ Arquitectura del Sistema

[cite_start]El proyecto sigue la metodología de diagrama de bloques requerida en el curso[cite: 70, 72]:

1.  [cite_start]**Calibración (Offline):** Corrección de la distorsión de la lente de la cámara.
2.  **Sistema de Seguridad (Bloque 1):**
    * [cite_start]**Detector de Patrones:** Identificación de formas (círculos, líneas)[cite: 57].
    * [cite_start]**Decodificador:** Lógica de estado que desbloquea la siguiente fase tras mostrar una secuencia correcta de 4 patrones[cite: 58].
    * *Uso en este proyecto:* [EXPLICA AQUÍ: Ej. "El usuario debe mostrar una secuencia de patrones impresa para 'armar' la alarma antes de dormir" o "Para apagar la alarma, además de despertarse, debe mostrar un código visual"].
3.  **Sistema Propuesto - Despertador (Bloque 2):**
    * [cite_start]**Tracker:** Algoritmo de seguimiento (Bounding Box) que detecta el movimiento del usuario al despertar.
    * **Lógica de Alarma:** La señal acústica persiste hasta que el tracker valida actividad sostenida.

---

## 🚀 Instalación y Requisitos

### Hardware
* [cite_start]Cámara Web o Cámara de Smartphone (conectada via IP/USB)[cite: 40, 50].
* Ordenador con capacidad de procesamiento de vídeo.

### Software
Este proyecto utiliza Python. Para instalar las dependencias necesarias:

```bash
pip install -r requirements.txt