// mentions-system.js
// Sistema de menciones reutilizable para formularios de comentarios y respuestas

class MentionSystem {
    constructor(textareaId, searchUrl) {
        this.textareaId = textareaId;
        this.textarea = document.getElementById(textareaId);
        
        // Extraer el sufijo del ID del textarea para los otros elementos
        // Ej: "commentTextarea" o "replyTextarea-123"
        const suffix = textareaId.includes('-') ? '-' + textareaId.split('-')[1] : '';
        
        this.dropdown = document.getElementById('mentionsDropdown' + suffix);
        this.list = document.getElementById('mentionsList' + suffix);
        this.loading = document.getElementById('mentionsLoading' + suffix);
        this.searchUrl = searchUrl;
        
        this.isActive = false;
        this.selectedIndex = 0;
        this.users = [];
        this.currentSearch = '';
        this.searchTimeout = null;
        
        if (!this.textarea) {
            console.warn(`⚠️ Textarea "${textareaId}" no encontrado`);
            return;
        }
        
        if (!this.dropdown || !this.list || !this.loading) {
            console.warn(`⚠️ Elementos de menciones no encontrados para "${textareaId}"`);
            return;
        }
        
        this.init();
    }
    
    init() {
        // Event listeners
        this.textarea.addEventListener('input', this.handleInput.bind(this));
        this.textarea.addEventListener('keydown', this.handleKeydown.bind(this));
        
        // Cerrar dropdown al hacer click fuera
        document.addEventListener('click', (e) => {
            if (!this.dropdown.contains(e.target) && e.target !== this.textarea) {
                this.hide();
            }
        });
        

    }
    
    handleInput(e) {
        const cursorPos = this.textarea.selectionStart;
        const textBeforeCursor = this.textarea.value.substring(0, cursorPos);
        const match = textBeforeCursor.match(/@(\w*)$/);
        
        if (match) {
            this.currentSearch = match[1];
            this.isActive = true;
            
            // Debounce search
            clearTimeout(this.searchTimeout);
            this.searchTimeout = setTimeout(() => {
                this.searchUsers(this.currentSearch);
            }, 300);
        } else {
            this.hide();
        }
    }
    
    async searchUsers(query) {
        this.showLoading();
        
        try {
            const response = await fetch(`${this.searchUrl}?q=${encodeURIComponent(query)}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            this.users = data.users || [];
            this.selectedIndex = 0;
            this.renderUsers();
            
        } catch (error) {
            console.error('Error buscando usuarios:', error);
            this.showError();
        }
    }
    
    renderUsers() {
        this.hideLoading();
        
        if (this.users.length === 0) {
            this.list.innerHTML = `
                <li class="px-4 py-3 text-sm text-muted text-center">
                    <i class="fas fa-search mb-2 text-2xl opacity-50"></i>
                    <p>No se encontraron usuarios</p>
                </li>
            `;
            this.show();
            return;
        }
        
        this.list.innerHTML = this.users.map((user, index) => `
            <li class="mention-item ${index === this.selectedIndex ? 'selected' : ''}" 
                data-index="${index}"
                data-username="${user.username}">
                <div class="flex items-center gap-3 px-3 py-2.5 cursor-pointer hover:bg-primary/10 transition-colors duration-150 border-b border-muted/10 last:border-b-0">
                    ${user.avatar ? 
                        `<img src="${user.avatar}" alt="${user.username}" class="w-8 h-8 rounded-full object-cover flex-shrink-0 border-2 border-primary/30">` :
                        `<div class="w-8 h-8 rounded-full bg-primary/20 text-primary flex items-center justify-center font-medium text-xs flex-shrink-0">${user.initials || user.username.charAt(0).toUpperCase()}</div>`
                    }
                    <div class="flex-1 min-w-0">
                        <p class="text-sm font-medium text-text truncate">@${user.username}</p>
                        ${user.full_name ? `<p class="text-xs text-muted truncate">${user.full_name}</p>` : ''}
                    </div>
                    <i class="fas fa-chevron-right text-xs text-muted/50"></i>
                </div>
            </li>
        `).join('');
        
        // Agregar event listeners a los items
        this.list.querySelectorAll('.mention-item').forEach(item => {
            item.addEventListener('click', () => {
                const username = item.getAttribute('data-username');
                this.insertMention(username);
            });
        });
        
        this.show();
    }
    
    handleKeydown(e) {
        if (!this.isActive || this.users.length === 0) return;
        
        switch(e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = (this.selectedIndex + 1) % this.users.length;
                this.updateSelection();
                break;
                
            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = (this.selectedIndex - 1 + this.users.length) % this.users.length;
                this.updateSelection();
                break;
                
            case 'Enter':
            case 'Tab':
                if (this.isActive && this.users.length > 0) {
                    e.preventDefault();
                    this.insertMention(this.users[this.selectedIndex].username);
                }
                break;
                
            case 'Escape':
                e.preventDefault();
                this.hide();
                break;
        }
    }
    
    updateSelection() {
        const items = this.list.querySelectorAll('.mention-item');
        items.forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                item.classList.remove('selected');
            }
        });
    }
    
    insertMention(username) {
        const cursorPos = this.textarea.selectionStart;
        const textBeforeCursor = this.textarea.value.substring(0, cursorPos);
        const textAfterCursor = this.textarea.value.substring(cursorPos);
        
        // Reemplazar @búsqueda con @username
        const newTextBefore = textBeforeCursor.replace(/@\w*$/, `@${username} `);
        this.textarea.value = newTextBefore + textAfterCursor;
        
        // Posicionar cursor después de la mención
        const newCursorPos = newTextBefore.length;
        this.textarea.setSelectionRange(newCursorPos, newCursorPos);
        this.textarea.focus();
        
        // Trigger auto-resize si existe la función
        if (typeof autoResize === 'function') {
            autoResize(this.textarea);
        }
        
        // Disparar evento input para que otros listeners se enteren
        this.textarea.dispatchEvent(new Event('input', { bubbles: true }));
        
        this.hide();
    }
    
    show() {
        this.dropdown.classList.remove('hidden');
    }
    
    hide() {
        this.dropdown.classList.add('hidden');
        this.isActive = false;
        this.users = [];
        this.currentSearch = '';
        this.selectedIndex = 0;
    }
    
    showLoading() {
        this.list.classList.add('hidden');
        this.loading.classList.remove('hidden');
        this.show();
    }
    
    hideLoading() {
        this.list.classList.remove('hidden');
        this.loading.classList.add('hidden');
    }
    
    showError() {
        this.hideLoading();
        this.list.innerHTML = `
            <li class="px-4 py-3 text-sm text-danger text-center">
                <i class="fas fa-exclamation-triangle mb-2 text-2xl"></i>
                <p>Error al buscar usuarios</p>
            </li>
        `;
        this.show();
    }
    
    // Método público para destruir la instancia
    destroy() {
        if (this.textarea) {
            this.textarea.removeEventListener('input', this.handleInput.bind(this));
            this.textarea.removeEventListener('keydown', this.handleKeydown.bind(this));
        }
        this.hide();
        console.log(`🗑️ Sistema de menciones destruido para: ${this.textareaId}`);
    }
}

// Función helper para auto-resize de textareas (si no está definida globalmente)
if (typeof autoResize !== 'function') {
    window.autoResize = function(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
        if (textarea.value === '') {
            textarea.style.height = 'auto';
        }
    };
}

// Exportar para uso en módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MentionSystem;
}