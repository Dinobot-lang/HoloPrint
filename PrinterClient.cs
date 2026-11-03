using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

// Chiede lo stato al gateway una volta al secondo e lo rende disponibile al resto dell'app.
public class PrinterClient : MonoBehaviour
{
    [Tooltip("Indirizzo del gateway sul PC, es. http://192.168.1.50:8080/state")]
    public string gatewayUrl = "http://192.168.1.50:8080/state";
    public float pollSeconds = 1f;

    [Tooltip("Oltre questi secondi senza messaggi dalla stampante i dati sono 'non aggiornati'. " +
             "Il gateway chiede lo stato ogni 30 s, quindi 45 e' un valore sicuro.")]
    public float maxAgeSeconds = 45f;

    public PrinterState Current { get; private set; }
    public bool HasData { get; private set; }
    public string LastError { get; private set; } = "";
    public event Action<PrinterState> StateUpdated;

    float lastOkTime = -999f;

    public bool IsStale
    {
        get
        {
            if (!HasData || Current == null) return true;
            if (Time.realtimeSinceStartup - lastOkTime > 5f) return true;  // gateway non raggiungibile
            if (!Current.connected) return true;                           // gateway senza stampante
            if (Current.age_s < 0f || Current.age_s > maxAgeSeconds) return true;
            return false;
        }
    }

    IEnumerator Start()
    {
        var wait = new WaitForSecondsRealtime(pollSeconds);
        while (true)
        {
            using (var req = UnityWebRequest.Get(gatewayUrl))
            {
                req.timeout = 3;
                yield return req.SendWebRequest();

                if (req.result == UnityWebRequest.Result.Success)
                {
                    try
                    {
                        Current = JsonUtility.FromJson<PrinterState>(req.downloadHandler.text);
                        HasData = Current != null;
                        lastOkTime = Time.realtimeSinceStartup;
                        LastError = "";
                        StateUpdated?.Invoke(Current);
                    }
                    catch (Exception e)
                    {
                        LastError = "JSON: " + e.Message;
                        Debug.LogWarning("HoloPrint: " + LastError);
                    }
                }
                else
                {
                    LastError = req.error;
                    Debug.LogWarning("HoloPrint: " + req.error);
                }
            }
            yield return wait;
        }
    }
}
