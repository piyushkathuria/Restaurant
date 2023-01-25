from rest_framework.response import Response
from food.serializer import *
from rest_framework.generics import GenericAPIView
from food.renderers import UserRenderer
from food.helper import get_distance
from meal_req.models import *
from meal_req.serializer import *
from collections import OrderedDict
import datetime
from rest_framework.views import APIView


class UserAddressDetail(APIView):
  serializer_class = RequestMedicineSerializer
  renderer_classes = [UserRenderer]
  def post(self,request,id):
    try:
      user = User.objects.get(id=id)
      phone_no = request.data.get('phone_no')
      address = request.data.get('address')
      latitude = request.data.get('latitude')
      longitude = request.data.get('longitude')
      cart_item = Cartitems.objects.filter(user=user)
      meal = RequestMedicine.objects.create(user=user,phone_no=phone_no,address=address,latitude=latitude,longitude=longitude,date=datetime.datetime.now)
      meal.cart.set(cart_item)
      meal.save()
      store = StoreInfo.objects.get(id=id)
      # create the order by the user to request the medicine by the request medicine table
      order = OrderStatus.objects.create(cart = meal,store_info= store) # validate name
      order.save()
      # order.cart.set(set(cart_item['id']))
      serializer = OrderStatusSerializer(order)
      return Response({"msg":"success","data":serializer.data})
    except:
      return Response({"status":"User Not Found"}, status = 400)

class UpdateUserAddressDetail(GenericAPIView):
  serializer_class = RequestMedicineSerializer
  renderer_classes = [UserRenderer]
  def put(self,request,id):
    try:
      user = User.objects.get(id=id)
      order = RequestMedicine.objects.get(user=user)
      serializer = UpdateUserDetailSerializer(order,data=request.data)
      serializer.is_valid(raise_exception=True)
      serializer.save()
      return Response({"status":"success", "data": serializer.data}, status = 200)
    except:
      return Response({"status":"User Not Found"}, status = 400)


class ViewUserAddressDetail(GenericAPIView):
  serializer_class = RequestMedicineSerializer
  renderer_classes = [UserRenderer]
  def get(self,request,id):
    try:
      user = User.objects.get(id=id)
      detail = RequestMedicine.objects.filter(user=user)
      serializer = RequestMedicineSerializer(detail,many=True)
      return Response({"status": "success", "data": serializer.data}, status = 200)
    except:
      return Response({"status": "No cart"}, status = 400)


class DeleteUserAddressDetail(GenericAPIView):
  serializer_class = RequestMedicineSerializer
  renderer_classes = [UserRenderer]
  def post(self,request,id):
    try:
      user = User.objects.filter(id=id)
      cart = RequestMedicine.objects.all().delete()
      serializer = RequestMedicineSerializer(cart,many=True)
      return Response({"status": "Deleted successfully", "data": serializer.data}, status = 200)
    except:
      return Response({"status": "Delete"}, status = 400)



class RadiusFind(GenericAPIView):
  serializer_class = OrderStatusSerializer
  renderer_classes = [UserRenderer]
  def get(self,request,id):
    try:
      # check user is logged in or not
      if not self.request.user.is_authenticated:
        return Response({"msg":"No user Found"})
      order = OrderStatus.objects.filter(id=id).values('store_info')
      owner = StoreInfo.objects.filter(id=order[0]['store_info']).values('owner')
      # Get the order that was refused by pharmacy
      order =OrderStatus.objects.filter(id=id).values()
      # Medicine requested bt the user
      medicine_value = RequestMedicine.objects.filter(id=order[0]['cart_id']).values() # and user id
      # getting the latitude and longitude of user location
      start1 = medicine_value[0]['latitude']
      start2 = medicine_value[0]['longitude']
      # get all the stores from database(for poc only,afterwards will filter within the radius of user
      res = StoreInfo.objects.all().values()
      dict = {}
      for i in range(len(res)):
        # distance of store from the user in km 
        end1 = float(res[i]["latitude"])
        end2 = float(res[i]["longitude"])
        distance = get_distance(start1,start2,end1,end2)
        #  if distance of stor and user is less than 10km order approved other wise in the else condition/
        if distance<=5:
          order = OrderStatus.objects.get(id=id)
          # order Accepted 
          order.status= "order_accepted"
          # order status table updated when the pharmacy accepted the order. 
          # converted the data into json.
          order.save()
          serializer = OrderStatusSerializer(OrderStatus.objects.filter(id=id),many=True)
          return Response({"msg":"Order Accepted","data":serializer.data},status=200)
        # In else order delined because the distance of store and user is  greater than 10km.
        order = OrderStatus.objects.get(id=id)
        # order status update.
        order.status = "order_not_accepted"
        # order status save in the order status table
        # order status save in the order status table
        order.save()
        # serialize the dtaa in the json form.
        serializer = OrderStatusSerializer(order)
        return Response({"msg":"Order Not Accepted","data":serializer.data},status=404)
      return Response({"msg":"You are not authorized"},status=404)
    except: 
      return Response({"msg":"No Order"},status=404)


class OrderAssignToDeliveryBoy(GenericAPIView):
  serializer_class = DeliveryBoySerializer
  renderer_classes = [UserRenderer]
  def post(self,request,id):
    try:
      # check the user is logged in or not.
      if not self.request.user.is_authenticated:
        return Response({'msg':'user not found'})
      # get the user in id is implement in the url.
      user = User.objects.get(id=id)
      # Get the id of order 
      order = RequestMedicine.objects.get(id=request.data.get('order'))
      # Get the delivery boy and crete the delovery order to that person
      delivery = DeliveryBoy.objects.create(user=user,order=order)
      delivery.save()
      serializer = DeliveryBoySerializer(delivery)
      return Response({"msg": "Order placed","data":serializer.data})
    except:
      return Response({"status": "Order Not Found"}, status = 400)


class OrderAssignGet(GenericAPIView):
  serializer_class = DeliveryBoySerializer
  renderer_classes = [UserRenderer]
  def get(self,request,id):
    try:
      if not self.request.user.is_authenticated:
        return Response({'msg':'user not found'})
      user = User.objects.get(id=id)
      delivery = DeliveryBoy.objects.filter(user=user)
      serializer = DeliveryBoySerializer(delivery,many=True)
      return Response({"status": "success", "data": serializer.data}, status = 200)
    except:
      return Response({"status": "Order Not Found"}, status = 400)


class DeliveryBoyOrderDelivered(GenericAPIView):
  serializer_class = OrderStatusSerializer
  renderer_classes = [UserRenderer]
  def post(self,request,id):
    try:
      if not self.request.user.is_authenticated:
        return Response({'msg':'user not found'})
      order =OrderStatus.objects.filter(id=id).values()
      medicine_value = RequestMedicine.objects.filter(id=order[0]['cart_id']).values() # and user id
      med_lat = medicine_value[0]['latitude']
      med_lon = medicine_value[0]['longitude']
      res = RequestMedicine.objects.all().values()
      dict = {}
      for i in range(len(res)):
        store_lat = float(res[i]["latitude"])
        store_lon = float(res[i]["longitude"])
        distance = get_distance(med_lat,med_lon,store_lat,store_lon)
        dict[distance] = res[i]
      dict1 = OrderedDict(sorted(dict.items()))
      req_med = RequestMedicine.objects.filter(id=order[0]['cart_id']).values()
      index = list(dict1.values()).index(req_med[0])
      if index+1 >=list(dict1.values()).index(req_med[0]):
        order = OrderStatus.objects.get(id=id)
        order.status = 'delivered'
        order.save()
        return Response({'msg':"order delivered"},status=200)
      serializer = OrderStatusSerializer(order)
      return Response({'msg':"order delivered","data": serializer.data},status=200)
    except:
      return Response({'msg':"Order Not Found"},status=400)


class DeliveryBoyOrderGet(GenericAPIView):  
  renderer_classes = [UserRenderer]
  def get(self,request):
    try:
      if not self.request.user.is_authenticated:
        return Response({'msg':'user not found'})
      delivery = DeliveryBoy.objects.filter(user=self.request.user)
      serializer = DeliveryBoySerializer(delivery,many=True)
      return Response({"status": "success", "data": serializer.data}, status= 200)
    except:
      return Response({"msg":"Order not found"})


class FoodOrderApporve(GenericAPIView):
  serializer_class = RequestMedicineSerializer
  renderer_classes = [UserRenderer]
  def post(self,request,id):
    """
    :return: Approve the order by pharmacy.
    """
    try:
      if not self.request.user.is_authenticated:
        return Response({"msg":"No user Found"})
        # Request the user to have permission to change the order status.
      if self.request.user.has_perm('meal_req.change_orderstatus'):
        # Get the order id in the order status table.
        order = OrderStatus.objects.filter(id=id).values('store_info')
        owner = StoreInfo.objects.filter(id=order[0]['store_info']).values('owner')
        if owner[0]['owner'] == self.request.user.id:  
          order = OrderStatus.objects.get(id=id)
          # order Accepted 
          order.status= "order_accepted"
          # order status table updated when the pharmacy accepted the order. 
          # converted the data into json.
          order.save()
          serializer = OrderStatusSerializer(OrderStatus.objects.filter(id=id),many=True)
          return Response({"status": "Success", "data": serializer.data}, status=200)
        return Response({"status": "You are not authorized"}, status=203)
      return Response({"status": "You are not authorized"}, status=203)
    except:
      return Response ({"status": "Order Not Found"}, status=203)


class FoodOrderDecline(GenericAPIView):
  serializer_class = RequestMedicineSerializer
  renderer_classes = [UserRenderer]
  def post(self,request,id):
    """
    :return: To decline the order of medicine ordered by the customer.
    """
    try:
      if not self.request.user.is_authenticated:
        return Response({"msg":"No user Found"})
        # Request the user to have permission to change the order status.
      if self.request.user.has_perm('meal_req.change_orderstatus'):
        # Get the order id in the order status table.
        order = OrderStatus.objects.filter(id=id).values('store_info')
        owner = StoreInfo.objects.filter(id=order[0]['store_info']).values('owner')
        if owner[0]['owner'] == self.request.user.id:  
          order = OrderStatus.objects.get(id=id)
          # order Accepted 
          order.status= "order_not_accepted"
          order.save()
          serializer = OrderStatusSerializer(OrderStatus.objects.filter(id=id),many=True)
          return Response({"status": "Success", "data": serializer.data}, status=200)
        return Response({"status": "You are not authorized"}, status=203)
      return Response({"status": "You are not authorized"}, status=203)
    except:
      return Response ({"status": "Order Not Found"}, status=203)