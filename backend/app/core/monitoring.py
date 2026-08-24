"""
MITRA Monitoring & Observability
---------------------------------
OpenTelemetry + Prometheus integration for production monitoring.
"""
from __future__ import annotations

import os
import time
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Lazy initialization - only import when monitoring is enabled
_tracer = None
_meter = None
_prometheus_metrics = None
_monitoring_enabled = False


def init_monitoring():
    """
    Initialize OpenTelemetry and Prometheus monitoring.
    Called once at startup if monitoring is enabled.
    """
    global _tracer, _meter, _prometheus_metrics, _monitoring_enabled

    if _monitoring_enabled:
        return

    try:
        from opentelemetry import trace, metrics
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.sdk.resources import SERVICE_NAME, Resource

        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        service_name = os.getenv("OTEL_SERVICE_NAME", "mitra-core")
        environment = os.getenv("OTEL_ENVIRONMENT", "production")

        resource = Resource.create({
            SERVICE_NAME: service_name,
            "deployment.environment": environment,
        })

        # Tracing
        trace_provider = TracerProvider(resource=resource)
        try:
            trace_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            trace_provider.add_span_processor(BatchSpanProcessor(trace_exporter))
        except Exception as e:
            logger.warning(f"OTLP trace exporter failed: {e}")
        trace.set_tracer_provider(trace_provider)
        _tracer = trace.get_tracer(service_name)

        # Metrics
        try:
            metric_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
            metric_reader = PeriodicExportingMetricReader(metric_exporter, export_interval_millis=10000)
            meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
            metrics.set_meter_provider(meter_provider)
            _meter = metrics.get_meter(service_name)
        except Exception as e:
            logger.warning(f"OTLP metric exporter failed: {e}")

        _monitoring_enabled = True
        logger.info(f"OpenTelemetry monitoring initialized: {service_name} @ {otlp_endpoint}")

    except ImportError:
        logger.warning("OpenTelemetry packages not installed. Monitoring disabled.")
    except Exception as e:
        logger.error(f"Failed to initialize monitoring: {e}")


def init_prometheus_metrics(app):
    """
    Initialize Prometheus metrics with FastAPI.
    Adds /metrics endpoint and auto-instruments all routes.
    """
    global _prometheus_metrics

    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

        instrumentator = Instrumentator(
            should_group_status_codes=False,
            should_ignore_untemplated=True,
            excluded_handlers=["/metrics", "/health"],
        )
        instrumentator.instrument(app)
        instrumentator.expose(app, endpoint="/metrics")

        _prometheus_metrics = True
        logger.info("Prometheus metrics initialized")

    except ImportError:
        logger.warning("Prometheus packages not installed. Metrics disabled.")
    except Exception as e:
        logger.error(f"Failed to initialize Prometheus metrics: {e}")


def get_tracer():
    """Get the OpenTelemetry tracer."""
    return _tracer


def get_meter():
    """Get the OpenTelemetry meter."""
    return _meter


def create_span(name: str, attributes: Optional[dict] = None):
    """Create an OpenTelemetry span if monitoring is enabled."""
    if _tracer:
        span = _tracer.start_span(name)
        if attributes:
            for k, v in attributes.items():
                span.set_attribute(k, str(v))
        return span
    return None
