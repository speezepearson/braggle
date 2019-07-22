import Browser
import Dict
import Html exposing (Attribute, Html, node, text)
import Html.Attributes exposing (attribute)
import Html.Events exposing (onClick, onInput)
import Http
import Json.Decode as D
import Json.Encode as E

type alias Id = String
type Subtree = Ref Id | Text String | Node String (List (Attribute Msg)) (List Subtree)
type alias Element =
    { id : Id
    , subtree : Subtree
    }

subtreeDecoder : D.Decoder Subtree
subtreeDecoder =
    D.oneOf
        [ D.map Ref (D.field "ref" D.string)
        , D.map Text (D.field "text" D.string)
        , D.map3 Node
            (D.field "name" D.string)
            (D.field "attributes" (D.list (D.map2 attribute (D.index 0 D.string) (D.index 1 D.string))))
            (D.field "children" (D.list (D.lazy (\_ -> subtreeDecoder))))
        ]
elementDecoder : D.Decoder Element
elementDecoder =
    D.map2 Element
        (D.field "id" D.string)
        (D.field "subtree" subtreeDecoder)
pollDecoder: D.Decoder Msg
pollDecoder =
    D.map3 PollCompleted
        (D.field "root" D.string)
        (D.field "timeStep" D.int)
        (D.field "elements" (D.dict elementDecoder))

type alias TimeStep = Int
type alias Model =
    { elements : Dict.Dict Id Element
    , timeStep : TimeStep
    , root : Id
    }
type Msg
    = Interacted Interaction
    | PollCompleted Id TimeStep (Dict.Dict Id Element)
    | PollFailed Http.Error
    | Ignore

type Interaction = Clicked Id | Inputted Id String

poll : TimeStep -> Cmd Msg
poll ts =
    let
        fromResult : Result Http.Error Msg -> Msg
        fromResult result = case result of
            Ok msg -> msg
            Err err -> PollFailed err
    in
        Http.post
            { url = "/poll"
            , body = Http.jsonBody (E.int ts)
            , expect = Http.expectJson fromResult pollDecoder
            }

notify : Interaction -> Cmd Msg
notify interaction =
    let
        payload : E.Value
        payload = case interaction of
            Clicked id -> E.object [("target", E.string id), ("type", E.string "click")]
            Inputted id value -> E.object [("target", E.string id), ("type", E.string "input"), ("value", E.string value)]
    in
        Http.post
            { url = "/interaction"
            , body = Http.jsonBody payload
            , expect = Http.expectWhatever (always Ignore)
            }

init : () -> (Model,  Cmd Msg)
init _ =
    ( { elements = Dict.singleton "root" {id="root", subtree=(Text "Loading...")}
      , timeStep = -1
      , root = "root"
      }
    , poll -1
    )

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        Interacted interaction -> (model, notify interaction)
        PollCompleted root timeStep elements ->
            ( { model
                | root = root
                , elements = model.elements |> Dict.union elements
                , timeStep = timeStep
                }
            , poll timeStep
            )
        PollFailed err -> Debug.todo (Debug.toString err)
        Ignore -> (model, Cmd.none)

view : Model -> Html Msg
view model =
    case Dict.get model.root model.elements of
        Nothing -> text "<NO ROOT?>"
        Just {id, subtree} -> viewSubtree model.elements id subtree

viewSubtree : Dict.Dict Id Element -> Id -> Subtree -> Html Msg
viewSubtree elements id subtree =
    case subtree of
        Text s -> Html.text s
        Node name attrs children ->
            let
                allAttrs = case name of
                    "button" -> onClick (Interacted (Clicked id)) :: attrs
                    "input" -> onInput (\val -> Interacted (Inputted id val)) :: attrs
                    _ -> attrs
            in
                Html.node name allAttrs (List.map (viewSubtree elements id) children)
        Ref refId -> case Dict.get refId elements of
            Nothing -> text "<NO ELEMENT?>"
            Just referent -> viewSubtree elements refId referent.subtree

main = Browser.element {init=init, update=update, view=view, subscriptions=(always Sub.none)}
