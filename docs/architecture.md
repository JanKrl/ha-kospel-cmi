# Architecture

System architecture for the Kospel Heater Home Assistant integration.

```mermaid
graph TB
    subgraph Integration["custom_components/kospel (this repo)"]
        HA[Home Assistant Entities]
        ConfigFlow[config_flow.py]
        Coordinator[coordinator.py]
        SensorEntity[sensor.py]
        ClimateEntity[climate.py]
        WaterHeaterEntity[water_heater.py]
    end

    subgraph Library["kospel-cmi-lib (external)"]
        EkcoM3[EkcoM3 device]
        Backend[Http or YAML backend]
        Registers[registers - decoders encoders enums utils]
    end

    subgraph External["External Systems"]
        HeaterAPI[Kospel Heater HTTP API]
    end

    HA --> Coordinator
    Coordinator --> EkcoM3
    ClimateEntity --> EkcoM3
    SensorEntity --> EkcoM3
    WaterHeaterEntity --> EkcoM3

    EkcoM3 --> Backend
    Backend --> Registers
    Backend --> HeaterAPI
```
