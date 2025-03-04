/* 
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - July 28th, 2023
 * Last Edited - July 28th, 2023 by Ben Schuster
 * Description - Global difficulty manager that observes difficulty and sends update events
 * to those that request it
 * ================================================================================================
 */
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Interface for observing difficulty
/// </summary>
public interface IDifficultyObserver
{
    /// <summary>
    /// Get the new difficulty modifier and apply it
    /// </summary>
    /// <param name="newModifier">new modifier to apply</param>
    void UpdateDifficulty(float newModifier);
}

/// <summary>
/// Difficulty Presets.
/// </summary>
[System.Serializable]
public struct DifficultyPreset
{
    [Tooltip("Name for this difficulty. Pascal Case.")]
    public string difficultyName;
    [Tooltip("Values in the following order: " +
        "Enemy Health, Enemy Damage, Projecitle Speed, Spawn Numbers, " +
        "Health Efficiency, Time Efficiency, Aim Assist")]
    public float[] defaultValues;
}

public class GlobalDifficultyManager : MonoBehaviour
{
    /// <summary>
    /// Global difficuklty manager instance. Handles distributing changes to difficulty
    /// </summary>
    public static GlobalDifficultyManager instance;

    /// <summary>
    /// Dictionary used to track settings and observers.
    /// KEY - string of the setting key
    /// VALUE - list of all current subscribers
    /// </summary>
    private Dictionary<string, List<IDifficultyObserver>> difficulties;

    /// <summary>
    /// Channel called when any setting is changed. String passed through is its key.
    /// </summary>
    public ChannelString onDifficultySettingChange;

    /// <summary>
    /// key used to look up difficulty version
    /// </summary>
    private const string difficultyVersionKey = "difficultyVersion";
    /// <summary>
    /// current version of the difficulty system.
    /// Changing this will force an update on new builds, useful if the player prefs cause bugs
    /// When saved in player prefs, this is hashed
    /// 
    /// FORMAT:
    /// diff_#.#
    /// </summary>
    private const string difficultyVersion = "diff_1.0";

    /// <summary>
    /// List of settings available for use
    /// note: Changing these involves changing the UI setting ref AND ref used by 
    /// concrete implementation of these settings
    /// </summary>
    private readonly string[] settingKeys = 
    {
        "PlayerDamage",
        "PlayerDamageVulnerability",
        "EnemyProjectileSpeed",
        "EnemyBudget",
        "HealthReplenishRate",
        "TimeReplenishRate",
        "AimAssistStrength"
    };

    [SerializeField] DifficultyPreset[] difficultyModes;

    private void Awake()
    {
        if(instance == null)
        {
            instance = this;
            DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
            return;
        }

        PrepareSettingLookup();

        // if they do not have a version, or the version does not match, update it
        if (!PlayerPrefs.HasKey(difficultyVersionKey)
            || PlayerPrefs.GetInt(difficultyVersionKey) != difficultyVersion.GetHashCode())
        {
            PlayerPrefs.SetInt(difficultyVersionKey, difficultyVersion.GetHashCode());
            SetDefaultDifficulties();
            Debug.Log($"[DifficultyManager] New difficulty version detected: {difficultyVersion}, resetting difficulty settings");
        }
    }

    private void OnEnable()
    {
        if (this != instance) return;

        onDifficultySettingChange.OnEventRaised += UpdateSettings;
    }

    private void OnDisable()
    {
        if (this != instance) return;

        onDifficultySettingChange.OnEventRaised -= UpdateSettings;
    }

    /// <summary>
    /// Set all saved difficulty keys to default value of 100 (for 100%)
    /// </summary>
    private void SetDefaultDifficulties()
    {
        foreach (var setting in settingKeys)
        {
            PlayerPrefs.SetFloat(setting, 100f);
        }
    }
    /// <summary>
    /// Set the difficulty mode. 
    /// </summary>
    /// <param name="difficultyName">Name of difficulty to set. PascalCase</param>
    public void SetDifficultyMode(string difficultyName)
    {
        // Do lookup to find the target difficulty mode
        int diffIdx;
        for (diffIdx = 0; diffIdx < difficultyModes.Length; diffIdx++)
        {
            if (difficultyModes[diffIdx].difficultyName == difficultyName)
                break;
        }
        
        // make sure one was found, otherwise throw an error and exit
        // catches edge case of loop completing without finding a match
        if (difficultyModes[diffIdx].difficultyName != difficultyName)
        {
            Debug.Log("[GlobalDifficultyManager] ERROR! An attempt to set difficulty mode {difficultyName} has failed!" +
                "Please make sure it was spelled the same way it is in GlobalDifficultyManager's difficultyModes. It should be pascal case");
            return;
        }

        // set settings appropriately
        for(int i = 0; i < settingKeys.Length; i++)
        {
            PlayerPrefs.SetFloat(settingKeys[i], difficultyModes[diffIdx].defaultValues[i]);
            UpdateSettings(settingKeys[i]);
        }
    }

    /// <summary>
    /// Prepare the dictionary lookup
    /// </summary>
    private void PrepareSettingLookup()
    {
        difficulties = new Dictionary<string, List<IDifficultyObserver>>();
        for (int i = 0; i < settingKeys.Length; i++)
        {
            difficulties.Add(settingKeys[i], new List<IDifficultyObserver>());
        }
    }

    /// <summary>
    /// Get the new value, tell each subscriber to update as well
    /// </summary>
    /// <param name="modifiedSetting">Key of setting to update</param>
    private void UpdateSettings(string modifiedSetting)
    {
        // if not a valid setting, return
        if (!difficulties.ContainsKey(modifiedSetting))
        {
            Debug.Log($"[DifficultyManager] Tried to update setting {modifiedSetting}, but not results." +
                $" Double check it spelling, and make sure its added to this manager's options.");
            return;
        }
        
        // get ref to subscribers
        float newModifier = (PlayerPrefs.GetFloat(modifiedSetting, 100)/100);
        List<IDifficultyObserver> group = difficulties[modifiedSetting];
        //Debug.Log($"Updating Setting {modifiedSetting} to {newModifier}");

        // tell each subscriber to update its settings
        foreach (IDifficultyObserver observer in group)
        {
            observer.UpdateDifficulty(newModifier);
        }
    }

    /// <summary>
    /// Subscribe to difficulty manager to recieve updates from difficulty manager.
    /// Will also update its current modifer
    /// </summary>
    /// <param name="o">Observer to subscribe</param>
    /// <param name="settingKey">Difficulty setting to use</param>
    public void Subscribe(IDifficultyObserver o, string settingKey)
    {
        if(difficulties.ContainsKey(settingKey) && !difficulties[settingKey].Contains(o))
        {
            difficulties[settingKey].Add(o);

            // on subscribe, give it the current difficulty setting so its not out of date
            float modifier = (PlayerPrefs.GetFloat(settingKey, 100) / 100);
            //Debug.Log($"Updating Setting {settingKey} to {modifier}");
            o.UpdateDifficulty(modifier);
        }
    }

    /// <summary>
    /// Unsubscribe fromm the manager to be unaffected by difficulty. WIll reset its modifier to 1
    /// </summary>
    /// <param name="o">Object unsubscribing</param>
    /// <param name="settingKey">Difficulty key to check</param>
    public void Unsubscribe(IDifficultyObserver o, string settingKey)
    {
        if (difficulties.ContainsKey(settingKey) && difficulties[settingKey].Contains(o))
        {
            difficulties[settingKey].Remove(o);

            // on unsubscribe, reset its difficulty modifier to flat 1
            o.UpdateDifficulty(1);
        }
    }
}
