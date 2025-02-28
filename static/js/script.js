class ChatBot {
    constructor() {
        this.messages = [];
        this.currentStep = 'greeting';
        this.searchParams = {};
        this.isLoading = false;

        // DOM Elements
        this.messagesContainer = document.getElementById('messages');
        this.userInput = document.getElementById('user-input');
        this.sendButton = document.getElementById('send-btn');
        this.actionButtons = document.getElementById('action-buttons');
        this.confirmButton = document.getElementById('confirm-btn');
        this.cancelButton = document.getElementById('cancel-btn');
        this.loadingContainer = document.querySelector('.loading-container');

        // Animation elements
        this.botCharacter = document.querySelector('.bot-character');
        this.shoppingCart = document.querySelector('.shopping-cart');
        this.products = document.querySelectorAll('.product');
        this.progressFill = document.querySelector('.progress-fill');
        this.progressText = document.querySelector('.progress-text');

        // Bind event listeners
        this.sendButton.addEventListener('click', () => this.handleSend());
        this.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSend();
        });
        this.confirmButton.addEventListener('click', () => this.startSearch());
        this.cancelButton.addEventListener('click', () => this.resetChat());

        // Start the chat
        this.init();
    }

    init() {
		this.addMessage({
				text: `Hello! I'm your smart shopping assistant.️  
			I'll help you find the best deals and prices from various online stores.  
			How can I assist you today? 😊`,
				sender: 'bot'
			});


        setTimeout(() => {
            this.addMessage({
                text: 'What product are you looking for? 🔍',
                sender: 'bot'
            });
            this.currentStep = 'product';
        }, 1000);
    }

    addMessage(message) {
        this.messages.push(message);
        
        const messageElement = document.createElement('div');
        messageElement.className = `message ${message.sender}`;
        messageElement.innerHTML = `
            <div class="message-content">${message.text}</div>
        `;
        
        this.messagesContainer.appendChild(messageElement);
        this.scrollToBottom();

        gsap.from(messageElement, {
            duration: 0.5,
            opacity: 0,
            y: 20,
            ease: "power2.out"
        });
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    startLoadingAnimation() {
        this.loadingContainer.style.display = 'block';
        
        // Reset animations
        gsap.set([this.botCharacter, this.shoppingCart, ...this.products], { clearProps: "all" });
        gsap.set(this.progressFill, { width: "0%" });
        
        // Create timeline
        const tl = gsap.timeline({
            repeat: -1,
            onUpdate: () => {
                const progress = Math.round((tl.progress() * 100));
                this.progressFill.style.width = `${progress}%`;
                this.progressText.textContent = `${progress}%`;
            }
        });

        // Animate bot and cart
        tl.to(this.botCharacter, {
            x: "+=200",
            duration: 2,
            ease: "power1.inOut"
        })
        .to(this.shoppingCart, {
            x: "-=200",
            duration: 2,
            ease: "power1.inOut"
        }, 0);

        // Animate products dropping into cart
        this.products.forEach((product, index) => {
            tl.to(product, {
                opacity: 1,
                y: 50,
                duration: 0.5,
                ease: "bounce.out"
            }, 0.5 + (index * 0.3));
        });

        return tl;
    }

    handleSend() {
        const text = this.userInput.value.trim();
        if (!text) return;

        this.addMessage({
            text: text,
            sender: 'user'
        });

        this.userInput.value = '';

        switch (this.currentStep) {
            case 'product':
                this.searchParams.productName = text;
                setTimeout(() => {
                    this.addMessage({
                        text: 'In which country would you like to search for the product? 🌍',
                        sender: 'bot'
                    });
                    this.currentStep = 'country';
                }, 1000);
                break;

            case 'country':
                this.searchParams.country = text;
                setTimeout(() => {
                    this.addMessage({
                        text: 'How many results would you like in the final report? 📊',
                        sender: 'bot'
                    });
                    this.currentStep = 'count';
                }, 1000);
                break;

            case 'count':
                const count = parseInt(text);
                if (isNaN(count)) {
                    this.addMessage({
                        text: 'Please enter a valid number. 🔢',
                        sender: 'bot'
                    });
                    return;
                }
                this.searchParams.resultCount = count;
                this.showSummary();
                break;
        }
    }

    showSummary() {
        const { productName, country, resultCount } = this.searchParams;
        this.addMessage({
            text: `I will search for 🔍 "${productName}" in ${country}, and I will provide you with a report featuring the best 📊✨ ${resultCount} results. Would you like me to start the search? 🔍🚀`,
            sender: 'bot'
        });
        
        this.currentStep = 'summary';
        document.getElementById('input-container').style.display = 'none';
        this.actionButtons.style.display = 'flex';
    }

    async startSearch() {
        this.currentStep = 'searching';
        this.actionButtons.style.display = 'none';
        document.getElementById('input-container').style.display = 'none';
        
        const loadingAnimation = this.startLoadingAnimation();

        try {
            // Simulate search process (3 stages)
            setTimeout(() => {
                this.addMessage({
                    text: 'Searching in online stores... 🔍🛒',
                    sender: 'bot'
                });
            }, 1000);

            setTimeout(() => {
                this.addMessage({
                    text: 'Multiple products found, comparing prices... 🔍💰',
                    sender: 'bot'
                });
            }, 3000);

            setTimeout(() => {
                this.addMessage({
                    text: 'Analyzing the best deals and preparing the final report... 📊✨',
                    sender: 'bot'
                });
            }, 5000);
            

            const response = await fetch('http://localhost:5000/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.searchParams)
            });
            
            const data = await response.json();

            // Complete search after 7 seconds
            setTimeout(() => {
                loadingAnimation.kill();
                this.loadingContainer.style.display = 'none';
                document.getElementById('input-container').style.display = 'flex';
                
                if (data.status === 'success') {
                    this.addMessage({
                        text: 'The report has been successfully generated! You can download the results now. 📄✅🚀',
                        sender: 'bot'
                    });
                

                    const downloadBtn = document.createElement('a');
                    downloadBtn.className = 'download-btn';
                    downloadBtn.href = data.report_url;
                    downloadBtn.textContent = "Download the report";
                    downloadBtn.target = "_blank";
                    downloadBtn.download = "procurement_report.html";
                
                    this.messagesContainer.appendChild(downloadBtn);
                
                    gsap.from(downloadBtn, {
                        duration: 0.5,
                        opacity: 0,
                        y: 20,
                        ease: "back.out(1.7)"
                    });
                }
                
                 else {
                    this.addMessage({ 
                        text: `An error occurred. ❌⚠️: ${data.message}`, 
                        sender: 'bot' 
                    });
                }
            }, 7000);

        } catch (error) {
            loadingAnimation.kill();
            this.loadingContainer.style.display = 'none';
            document.getElementById('input-container').style.display = 'flex';
            this.addMessage({ 
                text: 'An error occurred during the search. Please try again later. ❌🔄', 
                sender: 'bot' 
            });
        }
    }

    resetChat() {
        gsap.to([...this.messagesContainer.children], {
            duration: 0.3,
            opacity: 0,
            y: -20,
            stagger: 0.1,
            onComplete: () => {
                this.messages = [];
                this.currentStep = 'greeting';
                this.searchParams = {};
                this.messagesContainer.innerHTML = '';
                this.actionButtons.style.display = 'none';
                this.loadingContainer.style.display = 'none';
                document.getElementById('input-container').style.display = 'flex';
                this.init();
            }
        });
    }
}

// Initialize the chat bot
const chatBot = new ChatBot();