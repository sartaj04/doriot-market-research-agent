#!/bin/bash
export ENVIRONMENT=production
python -m app.core.celery.worker