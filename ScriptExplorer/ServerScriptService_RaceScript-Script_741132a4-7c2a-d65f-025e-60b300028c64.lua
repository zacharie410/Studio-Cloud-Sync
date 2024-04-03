print("I made these changes with visual studio!")
local RaceManager = require(391925754)
RaceManager:SetDebugEnabled(false)
RaceManager:SetIntermissionDuration(15)

local function pushNotificationForPlayer(player, message, duration)
	local notificationFrameContainer = player.PlayerGui.RaceNotificationScreen:FindFirstChild("NotificationFrameContainer")
	local notificationFrame = Instance.new("TextLabel", notificationFrameContainer)
	notificationFrame.Size = UDim2.new(1, 0, 1, 0)
	notificationFrame.Position = UDim2.new(0, 0, -1, 0)
	notificationFrame.Text = message
	for i, frame in ipairs(notificationFrameContainer:GetChildren()) do
		frame.Position = frame.Position + UDim2.new(0, 0, 1, 0)
	end
	delay(duration, function()
		for i = 1, 30 do
			notificationFrame.BackgroundTransparency = i / 30
			notificationFrame.TextTransparency = i / 30
			wait()
		end
		notificationFrame:Destroy()
	end)
end

local function pushNotification(message, duration)
	for _, player in ipairs(game.Players:GetPlayers()) do
		pushNotificationForPlayer(player, message, duration)
	end
end

local function onPlayerAdded(player)
	local playerGui = player:WaitForChild("PlayerGui")
	local raceNotificationScreen = Instance.new("ScreenGui", playerGui)
	raceNotificationScreen.Name = "RaceNotificationScreen"
	local notificationFrameContainer = Instance.new("Frame", raceNotificationScreen)
	notificationFrameContainer.Name = "NotificationFrameContainer"
	notificationFrameContainer.BackgroundTransparency = 1
	notificationFrameContainer.BorderSizePixel = 0
	notificationFrameContainer.Size = UDim2.new(0.3, 0, 0.1, 0)
	notificationFrameContainer.Position = UDim2.new(0.35, 0, 0, 0)
end

RaceManager.RaceStarted:connect(function()
	pushNotification("Race started!", 3)
end)

RaceManager.RaceFinished:connect(function(player)
	local message = "Race over. "
	if player then
		message = message .. player.Name .. " won!"
	else
		message = message .. " Ran out of time."
	end
	pushNotification(message, 5)
	wait(5)
	for _, player in ipairs(game.Players:GetPlayers()) do
		player:LoadCharacter()
		if game.StarterGui.ResetPlayerGuiOnSpawn then
			onPlayerAdded(player)
		end
	end
end)

RaceManager.IntermissionStarted:connect(function()
	local intermissionDuration = RaceManager:GetIntermissionDuration()
	wait(intermissionDuration / 2)
	pushNotification("Race starting soon!", intermissionDuration / 4)
end)

RaceManager.LapFinished:connect(function(player, lap, duration)
	local shortDuration = math.floor(tonumber(duration) * 1000) / 1000
	pushNotification(player.Name .. " finished lap " .. lap .. "/" .. RaceManager:GetNumLaps() .. " in " .. shortDuration .. " seconds", 2)
end)

for _, player in ipairs(game.Players:GetChildren()) do
	onPlayerAdded(player)
end
game.Players.PlayerAdded:connect(onPlayerAdded)