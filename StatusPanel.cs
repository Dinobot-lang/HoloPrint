using System.Text;
using TMPro;
using UnityEngine;

// Mostra lo stato della stampante nel pannello di testo.
public class StatusPanel : MonoBehaviour
{
    public PrinterClient client;
    public TMP_Text text;
    public float refreshSeconds = 0.5f;

    float nextRefresh;

    void Update()
    {
        if (text == null || Time.unscaledTime < nextRefresh) return;
        nextRefresh = Time.unscaledTime + refreshSeconds;
        text.text = Build();
    }

    // Verificati sulla stampante: IDLE, PREPARE, RUNNING, FINISH.
    // Da verificare: PAUSE, FAILED.
    static string StateLabel(string s)
    {
        switch (s)
        {
            case "IDLE": return "Pronta";
            case "PREPARE": return "Preparazione";
            case "RUNNING": return "In stampa";
            case "FINISH": return "Finita";
            case "PAUSE": return "In pausa";
            case "FAILED": return "Errore";
            default: return string.IsNullOrEmpty(s) ? "-" : s;
        }
    }

    string Build()
    {
        var sb = new StringBuilder();
        sb.AppendLine("<b>HoloPrint</b>");

        if (client == null || !client.HasData)
        {
            sb.AppendLine("In attesa del gateway...");
            if (client != null && !string.IsNullOrEmpty(client.LastError))
                sb.AppendLine("<size=70%>" + client.LastError + "</size>");
            return sb.ToString();
        }

        var s = client.Current;
        if (client.IsStale)
            sb.AppendLine("<color=#FF5555><b>DATI NON AGGIORNATI</b></color>");

        sb.AppendLine("Stato: <b>" + StateLabel(s.state) + "</b>");
        if (!string.IsNullOrEmpty(s.job)) sb.AppendLine(s.job);
        sb.AppendLine("Avanzamento: " + s.percent + "%   Layer " + s.layer + "/" + s.layers);
        sb.AppendLine("Tempo residuo: " + s.remain_min + " min");

        if (s.extruders != null)
            foreach (var e in s.extruders)
                sb.AppendLine("Ugello " + (e.id + 1) + ": " + e.temp + " / " + e.target + " °C");

        sb.AppendLine("Piano: " + s.bed.ToString("0") + " / " + s.bed_target.ToString("0") + " °C");
        sb.AppendLine("Camera: " + s.chamber.ToString("0") + " °C");
        sb.AppendLine("Velocità: livello " + s.speed_level + " (" + s.speed_percent + "%)");

        if (s.error != 0)
            sb.AppendLine("<color=#FF5555>Errore: " + s.error + "</color>");

        if (s.ams != null && s.ams.Length > 0)
        {
            sb.AppendLine("Filamenti:");
            foreach (var a in s.ams)
            {
                string rest = a.remain >= 0 ? a.remain + "%" : "?";
                string tipo = string.IsNullOrEmpty(a.type) ? "-" : a.type;
                int n;
                string slotNum = int.TryParse(a.slot, out n) ? (n + 1).ToString() : a.slot;
                sb.AppendLine("<mark=#" + a.color + "FF>   </mark> " + slotNum + ": " + tipo + " " + rest);
            }
        }
        return sb.ToString();
    }
}
