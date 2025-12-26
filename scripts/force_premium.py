"""
Script to FORCE UPGRADE a user to Premium.
Useful for testing when you don't have 'stripe listen' running locally.

Usage:
    python scripts/force_premium.py seu@email.com
"""
import sys
import os

# Add parent dir to path to import services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import update_user_premium

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Uso: python scripts/force_premium.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    print(f"🔄 Atualizando {email} para PREMIUM...")
    
    success = update_user_premium(email, True)
    
    if success:
        print(f"✅ Sucesso! O usuário {email} agora é PRO.")
        print("👉 Recarregue a página localhost:3000/pricing")
    else:
        print("❌ Erro ao atualizar. Verifique se o email existe no banco.")
