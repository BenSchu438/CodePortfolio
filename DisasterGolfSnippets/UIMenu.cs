
// HEADER REDACTED // 

public abstract class UIMenu : MonoBehaviour
{
	/// <summary>
	/// When enabled/opened, add itself to the menu stack
	/// </summary>
	private void OnEnable()
	{
		UIFlowManager.Instance.OpenMenu(this);
	}

	/// <summary>
	/// Called when closed via button. Removes the menu from the menu stack
	/// </summary>
	public virtual void ButtonClose()
	{
		UIFlowManager.Instance.RemoveMenu();
		Close();
	}

	/// <summary>
	/// Abstract class for closing the menu
	/// </summary>
	public abstract void Close();
}
