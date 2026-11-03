using System;

// Struttura dei dati inviati dal gateway (/state).
// I nomi dei campi devono coincidere ESATTAMENTE con le chiavi del JSON.

[Serializable]
public class ExtruderInfo
{
    public int id;
    public int temp;
    public int target;
}

[Serializable]
public class AmsSlot
{
    public string unit;
    public string slot;
    public string color;   // RRGGBB
    public string type;    // PLA, ABS, ...
    public string brand;
    public int remain;     // % residuo, -1 = sconosciuto
}

[Serializable]
public class PrinterState
{
    public bool connected;        // il gateway e' collegato alla stampante
    public float age_s;           // secondi dall'ultimo messaggio dalla stampante (-1 = mai)
    public string state;          // IDLE, PREPARE, RUNNING, FINISH, ...
    public string job;
    public int percent;
    public int remain_min;
    public int layer;
    public int layers;
    public float nozzle;          // ugello attivo
    public float nozzle_target;
    public ExtruderInfo[] extruders;
    public float bed;
    public float bed_target;
    public float chamber;
    public int speed_level;
    public int speed_percent;
    public string chamber_light;
    public string work_light;
    public AmsSlot[] ams;
    public int error;
    public string wifi;
}
