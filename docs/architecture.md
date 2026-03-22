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
        Ekco_M3[Ekco_M3 device]
        Backend[Http or YAML backend]
        Registers[registers - decoders encoders enums utils]
    end

    subgraph External["External Systems"]
        HeaterAPI[Kospel Heater HTTP API]
    end

    HA --> Coordinator
    Coordinator --> Ekco_M3
    ClimateEntity --> Ekco_M3
    SensorEntity --> Ekco_M3
    WaterHeaterEntity --> Ekco_M3

    Ekco_M3 --> Backend
    Backend --> Registers
    Backend --> HeaterAPI
```
