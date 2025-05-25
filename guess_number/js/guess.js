function checkNumber() {
    const guessNumber = parseInt(document.getElementById('guess').value);
    const message = document.getElementById('message');
    const triesDisplay = document.getElementById('tries');

    if (isNaN(guessNumber)) {
        message.innerHTML = "Please enter a valid number.";
        return;
    }

    if (guessNumber === random) {
        message.innerHTML = "Correct!";
    } else {
        if (tries > 1) {
            tries--;
            message.innerHTML = guessNumber > random ? " Lower!" : "Higher!";
        } else {
            message.innerHTML = "Game Over!";
            document.getElementById('guess').disabled = true; 
        }
    }

    triesDisplay.innerHTML = `Tries: ${tries}`;
}
    
    