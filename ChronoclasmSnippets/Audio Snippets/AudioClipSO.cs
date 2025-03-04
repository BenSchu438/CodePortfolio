/*
 * ================================================================================================
 * Author - Ben Schuster
 * Date Created - February 22nd, 2022
 * Last Edited - February 22nd, 2022 by Ben Schuster
 * Description - Custom data container for audio stuff
 * ================================================================================================
 */
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;
using UnityEngine.Audio;

[CreateAssetMenu(fileName = "New Audioclip Data", menuName = "Audio/Audioclip Data")]
public class AudioClipSO : ScriptableObject
{
    public enum PitchType
    {
        Range, 
        WeightedList
    }
    

    [InfoBox("Insert all potential audio clips you want to be played when this sound is called." +
        " When this sound is called, it will randomly select one of these clips to play. " +
        "The higher the weight of a clip, the more likely it will be selected.")]
    [Space(5)]


    [Header("=== Core Data ===")]

    [Tooltip("All clips to choose from")]
    [SerializeField] private GenericWeightedList<AudioClip> clips;

    [Tooltip("Which volume bus to play this audio within.")]
    [Required] public AudioMixerGroup volumeBus;

    [Tooltip("Priority of the audio clip. Lower number equals higher priority (golf scores).")]
    [Range(0, 256)] public int priority = 128;

    [Header("=== Volume ===")]

    [Tooltip("Base volume of this audio clip.")]
    [Range(0, 2)] public float volume = 1;

    [Tooltip("How pitch should be determined"), EnumToggleButtons]
    public PitchType pitchType;

    [Tooltip("Possible pitches to play audio at, random range style")]
    [ShowIf("@this.pitchType == PitchType.Range")]
    [MinMaxSlider(minValue:0.1f, maxValue:3, ShowFields = true)] 
    public Vector2 pitch = new Vector2(1, 1);

    [Tooltip("Possible pitches to play audio at, weighted list style.")]
    [ShowIf("@this.pitchType == PitchType.WeightedList")]
    [SerializeField] private GenericWeightedList<float> pitches;

    [Tooltip("Whether or not this audio clip should play looped."), Space(5)]
    public bool loop = false;

    [Header("=== Distance ===")]

    [Tooltip("How 3D is this audio. 1 is full 3D.")]
    [Range(0, 1)] public float spatialBlend = 0.8f;

    [Tooltip("How the distance scales, if being used. Linear recommended.")]
    public AudioRolloffMode distanceMode = AudioRolloffMode.Linear;

    [Tooltip("Minimum distance required to hear the audio at max volume.")]
    public float minDistance = 3;

    [Tooltip("Maximum distance required to hear the audio at all.")]
    public float maxDistance = 75;

    [Tooltip("Intensity of doppler. Determines pitch based on distance.")]
    [Range(0, 5)] public float doppler = 1;
    


    /// <summary>
    /// Get an audio clip from this pool of clips
    /// </summary>
    /// <returns>Randomly selected clip</returns>
    public AudioClip GetClip()
    {
        return clips.Pull();
    }
    /// <summary>
    /// Get a pitch for this clip, regardless of its type
    /// </summary>
    /// <returns>Randomly selected pitch</returns>
    public float GetPitch()
    {
        if(pitchType == PitchType.Range)
            return Random.Range(pitch.x, pitch.y);
        else
            return pitches.Pull();
    }
}
