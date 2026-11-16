# Dryad

Dryad is a smart forest monitoring tool designed to make forest conservation easier via 24/7 acoustic monitoring and a spatio-temporal risk prediction engine. This repository contains four main folders, each one corresponding to an aspect of the Dryad system. The entire functioning web application can be found in Fullstack Web App, with the other folders representing the various work that went into building the final system.

## Repository contents

| Folder | Contents |
| --- | --- |
| `Acoustic Classification Model/` | Audio-classification training and evaluation scripts, CNN model code, dataset resources and metadata, trained model files, and visualizations. Includes experiments with sound-event detection and a desktop live-audio demo. |
| `Continually Learning Model/` | Research code for Bayesian neural-network and Monte Carlo dropout risk prediction, synthetic data generation, model evaluation, and result visualizations. |
| `Fullstack Web App/` | The web platform: a Next.js frontend and Django/GeoDjango backend for geographic monitoring and project data, with GIS and machine-learning features. Also contains Docker configuration and scripts for running the app. |
| `Mock App/` | A Flutter mobile prototype with live audio classification and an ONNX model inference demo. |

These components can be explored and developed independently. Each project folder contains its own detailed setup guidance and relevant configuration.
