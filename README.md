# Smart Wake-Up System: Proyecto Final de Visión por Ordenador I

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.8.0.76-green)
![Status](https://img.shields.io/badge/Estado-En%20Desarrollo-yellow)

> **Institución:** Universidad Pontificia Comillas (ICAI) - Ingeniería Matemática<br>
> **Asignatura:** Visión por Ordenador I<br>
> **Curso:** 2025/2026

## 📖 Descripción del Proyecto

Este proyecto implementa un **sistema de despertar inteligente** basado en visión por ordenador. A diferencia de las alarmas tradicionales, este sistema monitoriza al usuario mientras duerme mediante una cámara y utiliza un tracker para verificar si se ha levantado.

Para garantizar que el usuario está completamente despierto y cognitivamente activo, el sistema integra un **módulo de seguridad** que impide desactivar la alarma hasta que se muestra a la cámara una secuencia específica de patrones visuales.

### 🎯 Funcionalidades Principales
1.  **Monitorización del sueño:** Uso de *tracking* para detectar la presencia o movimiento del usuario en la cama.
2.  **Validación de despertar:** La alarma persiste hasta que se cumple la condición de desbloqueo.
3.  **Desbloqueo por Patrones:** Decodificación de una secuencia visual (círculos/líneas) para desactivar el sistema (Requisito de Seguridad).

---

## ⚙️ Arquitectura del Sistema

El flujo de trabajo se divide en los siguientes bloques:

1.  **Calibración (Offline):**
    * Cálculo de la matriz intrínseca de la cámara y coeficientes de distorsión para corregir la entrada de vídeo.
    
2.  **Sistema Propuesto (Vigilancia):**
    * **Tracker:** Se inicializa una *Bounding Box* sobre el usuario. Si el tracker detecta movimiento significativo o la ausencia del usuario (al levantarse), se activa el estado de "Alerta/Validación".
    
3.  **Sistema de Seguridad (Desactivación):**
    * **Detector de Patrones:** Reconocimiento de formas geométricas básicas.
    * **Decodificador de Secuencia:** Lógica de estados que valida una secuencia ordenada (ej. Círculo -> Círculo -> Línea -> Línea). Solo al completar la secuencia correcta se apaga la alarma.

---

## 🚀 Requisitos e Instalación

### Hardware
* Webcam o cámara de Smartphone (conectada vía IP o USB).
* PC con entorno Python configurado.
* Patrones impresos o digitales (para la secuencia de desbloqueo).

### Software
Clonar el repositorio e instalar las dependencias:

```bash
git clone [https://github.com/usuario/smart-wake-up.git](https://github.com/usuario/smart-wake-up.git)
cd smart-wake-up
pip install -r requirements.txt