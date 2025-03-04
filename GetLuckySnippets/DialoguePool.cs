using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class DialoguePool : MonoBehaviour
{
    private List<DialogueOption> pool;
    [SerializeField] private List<DialogueOption> corePool;
    private DialogueOption lastUsed = null;
    private bool justRefreshed = false;

    private void Start()
    {
        pool = new List<DialogueOption>(corePool);
    }

    /// <summary>
    /// Get a dialogue from this pool
    /// </summary>
    /// <returns>Last dialogue option used</returns>
    public DialogueOption GetFromPool()
    {
        DialogueOption option;
        int r;
        // Select once. If it was recently refreshed, then make sure the last post isnt selected again
        do
        {
            r = Random.Range(0, pool.Count);
            option = pool[r];
        } while (justRefreshed && option == lastUsed);
        justRefreshed = false;
        pool.Remove(option);

        // Check if pool is empty. If empty, refresh
        if (pool.Count == 0)
        {
            Debug.Log("Out of text, refreshing " + name + " pool");
            pool = new List<DialogueOption>(corePool);
            justRefreshed = true;
            lastUsed = option;
        }
        return option;
    }
}
