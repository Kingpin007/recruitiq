from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(['GET'])
@permission_classes([AllowAny])
def current_user(request):
    """Get the current authenticated user's information."""
    if not request.user.is_authenticated:
        return Response({'detail': 'Not authenticated'}, status=status.HTTP_401_UNAUTHORIZED)
    
    user = request.user
    return Response({
        'email': user.email,
        'username': user.username if hasattr(user, 'username') else user.email.split('@')[0],
    })

