using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using TMPro;
using UnityEngine.UI;
using UnityEngine.SceneManagement;

/// <summary>
/// Manages uploading the dialogue to the UI elements
/// </summary>
public class DialogueManager : StateInteractor
{
    [Header("Dialogue Data")]
    [SerializeField] private List<DialoguePool> pools;
    [SerializeField] private DialoguePool successPool;
    [SerializeField] private DialoguePool failPool;
    [SerializeField] private DialoguePool expositionPool;
    /// <summary>
    /// Data from the first option
    /// </summary>
    private DialogueOption option1Data;
    /// <summary>
    /// Data from the second option
    /// </summary>
    private DialogueOption option2Data;
    /// <summary>
    /// Data from the reaction
    /// </summary>
    private DialogueOption reactData;

    [SerializeField] private List<string> currentLines;
    private List<Color> currentColors;
    [SerializeField] private float loadDelay;
    private int lineIndex;
    private bool loadingText;
    private Coroutine coroutineBuffer;

    [SerializeField] private Color LLColor;
    [SerializeField] private Color PCColor;
    
    [Header("Event Stuff")]
    [SerializeField] private DialogueOption gameIntroDialogue;
    [SerializeField] private DialogueOption gameWinDialogue;
    [SerializeField] private DialogueOption gameLoseDialogue;
    [SerializeField] private IconPopBehavior iconSystem;

    [Header("Channels")]
    [SerializeField] private IntIntChannel choiceStatChannel;
    [SerializeField] private BoolChannel dialogueSuccessChannel;
    [SerializeField] private VoidChannel nextDialogChannel;
    [SerializeField] private VoidChannel confirmStatChannel;
    [SerializeField] private IntChannel poseChannel;

    [Header("UI References")]
    [SerializeField] private TextMeshProUGUI option1;
    [SerializeField] private TextMeshProUGUI option2;
    [SerializeField] private TextMeshProUGUI dialogueBox;
    [SerializeField] private Image nextArrow;

    [Tooltip("Max amount of characters allowed in a box")]
    [SerializeField] private int textboxLimit;

    public enum DialogueState
    {
        Loading,
        Start,
        WaitingForRoll,
        PlayerChoice, 
        Response,
        End
    }
    [SerializeField] private DialogueState currState = DialogueState.Loading;

    private void Start()
    {
        currentLines = new List<string>();
    }

    private void StartDialogueManager(byte b = default)
    {
        StartCoroutine(DelayedStart());
    }

    private IEnumerator DelayedStart()
    {
        yield return new WaitForSeconds(0.1f);
        NextState(false);
    }

    protected override void OnStateChange(int arg0)
    {
        if (GameManager.Instance.CurrentState == GameManager.GameState.Talking
            && currState == DialogueState.WaitingForRoll)
        {
            Debug.Log("[DialogueManager] State change accepted, moving to player choice");
            NextState(false);
        }
    }

    protected override void OnEnable()
    {
        base.OnEnable();
        dialogueSuccessChannel.OnEventRaised += ChooseReactDialogue;
        nextDialogChannel.OnEventRaised += NextLine;
        confirmStatChannel.OnEventRaised += StartDialogueManager;
    }

    protected override void OnDisable()
    {
        base.OnDisable();
        dialogueSuccessChannel.OnEventRaised -= ChooseReactDialogue;
        nextDialogChannel.OnEventRaised -= NextLine;
        confirmStatChannel.OnEventRaised -= StartDialogueManager;
    }

    /// <summary>
    /// Move onto the next state and start the next function
    /// </summary>
    /// <param name="gameEnd"></param>
    private void NextState(bool gameEnd)
    {
        switch (currState)
        {
            case DialogueState.Loading:
                currState = DialogueState.Start;
                PrepDialogue(gameIntroDialogue);
                break;
            case DialogueState.Start:
                currState = DialogueState.WaitingForRoll;
                break;
            case DialogueState.WaitingForRoll:
                currState = DialogueState.PlayerChoice;
                PrepDialogue(expositionPool.GetFromPool());
                GetDialogueOptions();
                nextArrow.transform.parent.gameObject.SetActive(false);
                break;
            case DialogueState.PlayerChoice:
                // Text started by react func
                currState = DialogueState.Response;
                break;
            case DialogueState.Response:
                if (gameEnd)
                {
                    currState = DialogueState.End;
                    if (GameManager.Instance.CurrentState == GameManager.GameState.Win)
                        PrepDialogue(gameWinDialogue);
                    else
                        PrepDialogue(gameLoseDialogue);
                }
                else
                {
                    currState = DialogueState.WaitingForRoll;
                }
                break;
            case DialogueState.End:
                break;
        }
    }

    /// <summary>
    /// Get two dialogue options to choose from, load into dialogue
    /// </summary>
    private void GetDialogueOptions()
    {
        option1.GetComponentInParent<Button>().interactable = true;
        option2.GetComponentInParent<Button>().interactable = true;

        int opt1 = Random.Range(0, pools.Count);
        int opt2;
        do
        {
            opt2 = Random.Range(0, pools.Count);
        } while (opt1 == opt2);

        option1Data = pools[opt1].GetFromPool();
        option2Data = pools[opt2].GetFromPool();

        StartCoroutine(LoadText(option1, option1Data.dialogueShorthand, 0, PCColor));
        StartCoroutine(LoadText(option2, option2Data.dialogueShorthand, 0, PCColor));
    }

    /// <summary>
    /// Export the choice option and its stat to game manager
    /// </summary>
    /// <param name="option">The option selected. [1,2]</param>
    public void ExportChoice(int option)
    {
        option1.GetComponentInParent<Button>().interactable = false;
        option2.GetComponentInParent<Button>().interactable = false;

        if (option == 1)
        {
            iconSystem.EmotionPop(option1Data);
            PrepDialogue(option1Data);
            choiceStatChannel.RaiseEvent((int)option1Data.statID, option1Data.statVal);
        }
        else if (option == 2)
        {
            iconSystem.EmotionPop(option2Data);
            PrepDialogue(option2Data);
            choiceStatChannel.RaiseEvent((int)option2Data.statID, option2Data.statVal);
        }
    }

    /// <summary>
    /// Choose the react dialogue based on passed in info. 
    /// </summary>
    /// <param name="successful">Whether or not the calculation passed</param>
    private void ChooseReactDialogue(bool successful)
    {
        if (successful)
        {
            reactData = successPool.GetFromPool();
        }
        else
        {
            reactData = failPool.GetFromPool();
        }
    }

    /// <summary>
    /// Divide data to match the character limit. Submits data to currentLines
    /// </summary>
    /// <param name="data">Dialogue data holding the text</param>
    private void PrepDialogue(DialogueOption data)
    {
        nextArrow.transform.parent.gameObject.SetActive(true);
        string fulldata = data.dialogueFull;

        List<string> dividedLines = new List<string>();
        List<Color> dividedColors = new List<Color>();
        Color currentColor = LLColor;
        string word = "";
        string line = "";
        for (int i = 0; i < fulldata.Length; i++)
        {
            if (fulldata[i] == '#')
            {
                switch (fulldata[i + 1])
                {
                    case 'l':
                        currentColor = LLColor;
                        break;
                    case 'p':
                        currentColor = PCColor;
                        break;
                }

                i += 2;
            }
            // If a space, finish word, try adding to line
            if (fulldata[i] == ' ')
            {
                // If it fits, then add word to line
                if (word.Length + line.Length + 1 <= textboxLimit && fulldata[i] == ' ')
                {
                    if (line == "")
                        line = word;
                    else
                        line += ' ' + word;

                    word = "";
                }
                // If overflowing, then submit the line and start a new one
                else if (word.Length + line.Length + 1 > textboxLimit)
                {
                    dividedLines.Add(line);
                    dividedColors.Add(currentColor);
                    line = word;
                    word = "";
                }
            }
            // If an enter space and not overflowing, then add current word and start new line
            else if (fulldata[i] == '\n')
            {
                line += ' ' + word;
                dividedLines.Add(line);
                dividedColors.Add(currentColor);
                line = "";
                word = "";
            }
            else
            {
                word += fulldata[i];
            }
        }
        if (line == "")
            line = word;
        else
            line += ' ' + word;

        dividedLines.Add(line);
        dividedColors.Add(currentColor);
        currentLines = dividedLines;
        currentColors = dividedColors;
        lineIndex = 0;
        NextLine();
    }

    public void NextLine(byte b = default)
    {
        // If no dialogue, do nothing
        if (currentLines.Count <= 0 || 
            GameManager.Instance.CurrentState == GameManager.GameState.StatSelection)
            return;

        // If already loading the text, don't progress but instead instantly load it
        if(loadingText)
        {
            if(coroutineBuffer != null)
                StopCoroutine(coroutineBuffer);
            loadingText = false;
            dialogueBox.color = currentColors[lineIndex];
            dialogueBox.text = currentLines[lineIndex];
            lineIndex++;
        }
        // If reached final line, then send out a signal
        else if(lineIndex == currentLines.Count)
        {
            Debug.Log("Finished current dialogue! Calling state change!");
            nextArrow.transform.parent.gameObject.SetActive(false);
            dialogueBox.text = "";
            currentLines.Clear();

            if (currState == DialogueState.End)
            {
                LoadManager.Instance.LoadSingle("Endgame");
            }
            
            if (currState == DialogueState.PlayerChoice)
            {
                // submit reaction and the pose to be used
                PrepDialogue(reactData);
                poseChannel.RaiseEvent((int)reactData.pose);

            }
            else if (currState == DialogueState.Start)
            {
                requestStateChange.RaiseEvent((int)GameManager.GameState.SlideIn);
            }
            else if (currState == DialogueState.Response)
            {
                bool result = (GameManager.Instance.CurrentState == GameManager.GameState.Win
                || GameManager.Instance.CurrentState == GameManager.GameState.Lose);

                if(!result)
                    requestStateChange.RaiseEvent((int)GameManager.GameState.SlideIn);
            }

            NextState(GameManager.Instance.CurrentState == GameManager.GameState.Win 
                || GameManager.Instance.CurrentState == GameManager.GameState.Lose);
        }
        // Progress to the next line
        else
        {
            coroutineBuffer = StartCoroutine(LoadText(dialogueBox, currentLines[lineIndex], loadDelay, currentColors[lineIndex]));
        }
    }

    /// <summary>
    /// Load the dialogue into a target destination staggered
    /// </summary>
    /// <param name="target">target UI element to load the text</param>
    /// <param name="data">text to load</param>
    private IEnumerator LoadText(TextMeshProUGUI target, string data, float delay, Color textColor)
    {
        target.color = textColor;
        loadingText = true;
        string fulldata = data;
        string tempString = "";
        for(int i = 0; i < fulldata.Length; i++)
        {
            if (fulldata[i] == ' ' && i == 0)
                continue;

            tempString += fulldata[i];
            target.text = tempString;
            yield return new WaitForSecondsRealtime(delay);
            yield return null;
        }
        target.text = tempString;
        loadingText = false;
        lineIndex++;
    }
}
