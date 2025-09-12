#!/bin/bash

# Base directory for templates
TEMPLATE_DIR="/Users/charrcy/projects/WeedGo/microservices/ai-engine-service/src/Frontend/chat-commerce-web/src/templates"

# Function to copy WeedGo template and customize
create_template_from_weedgo() {
    local template_name=$1
    local theme_name=$2
    
    echo "Creating $template_name template..."
    
    # Copy WeedGo template
    cp -r "$TEMPLATE_DIR/weedgo" "$TEMPLATE_DIR/$template_name"
    
    # Update provider class name
    sed -i '' "s/WeedGoTemplateProvider/${theme_name}TemplateProvider/g" "$TEMPLATE_DIR/$template_name/provider.tsx"
    sed -i '' "s/super('weedgo')/super('$template_name')/g" "$TEMPLATE_DIR/$template_name/provider.tsx"
    
    # Update theme import
    sed -i '' "s/weedgoTheme/${template_name}Theme/g" "$TEMPLATE_DIR/$template_name/provider.tsx"
    sed -i '' "s/from '\.\/theme'/from '.\/theme'/g" "$TEMPLATE_DIR/$template_name/provider.tsx"
    
    echo "$template_name template created!"
}

# Create Vintage template
create_template_from_weedgo "vintage" "Vintage"

# Create Dirty template  
create_template_from_weedgo "dirty" "Dirty"

# Create Metal template
create_template_from_weedgo "metal" "Metal"

echo "All templates created successfully!"