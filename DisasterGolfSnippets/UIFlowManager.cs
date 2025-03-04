
// HEADER REDACTED //

/// <summary>
/// Manages the flow of the open menus and ensures only top menu is closed
/// </summary>
public class UIFlowManager : EnhancedSingleton<UIFlowManager>
{
	/// <summary>
	/// Player controller reference 
	/// </summary>
	private GameplayControls controls;
	/// <summary>
	/// Escape button input
	/// </summary>
	private InputAction esc;
	/// <summary>
	/// Stack of UIMenus opened
	/// </summary>
	private Stack<UIMenu> uiStack;

	/// <summary>
	/// Awake and initialize stack and inputs
	/// </summary>
	protected override void Awake()
	{
		base.Awake();
		uiStack = new Stack<UIMenu>();
		controls = new GameplayControls();
		esc = controls.Player.Escape;
		esc.performed += ctx => CloseMenu();
	}

	/// <summary>
	/// On enable, make sure this singleton esc is enabled
	/// </summary>
	private void OnEnable()
	{
		if (IsInstance(this))
		{
			esc.Enable();
		}
	}

	/// <summary>
	/// On disable, make sure this singleton esc is disabled
	/// </summary>
	private void OnDisable()
	{
		if (IsInstance(this))
		{
			esc.Disable();
		}
	}

	/// <summary>
	/// Push a menu into the stack
	/// </summary>
	/// <param name="menu">Menu to add to stack</param>
	public void OpenMenu(UIMenu menu)
	{
		uiStack.Push(menu);
	}

	/// <summary>
	/// Remove the top menu, but dont close it (button close)
	/// </summary>
	public void RemoveMenu()
	{
		if (uiStack.Count <= 0)
		{
			//Debug.Log("No menu to close");
			return;
		}
		// If pausing is locked, dont try to close panel to prevent a bug
		if (uiStack.Peek().gameObject.name == "Pause Panel" && GameManager.Instance.PauseLocked)
		{
			return;
		}
			uiStack.Pop();
	}

	/// <summary>
	/// Remove the top menu, call its close menu
	/// </summary>
	public void CloseMenu()
	{
		if (uiStack.Count <= 0)
		{
			//Debug.Log("No menu to close");
			return;
		}
		// If pausing is locked, dont try to close panel to prevent a bug
		if (uiStack.Peek().gameObject.name == "Pause Panel" && GameManager.Instance.PauseLocked)
		{
			return;
		}	
		uiStack.Pop().Close();
	}
}