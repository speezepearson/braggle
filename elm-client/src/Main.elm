import Browser
import Dict
import Html exposing (Attribute, Html, node, text)
import Html.Attributes exposing (attribute)
import Html.Events exposing (onClick, onInput)
import Http
import Json.Decode as D
import Json.Encode as E
import Url
import Url.Parser

import Bridge
import Protobuf.Decode
import Protobuf.Encode

type alias Id = String

type alias Timestep = Int

type alias Model =
    { serverState : { timestep: Timestep , root : Id , elements : Dict.Dict Id Element}
    }
type Msg
    = Interacted Interaction
    | PollCompleted Bridge.PartialServerState
    | PollFailed Http.Error
    | Ignore

must : Maybe a -> a
must mx =
    case mx of
        Just x -> x
        Nothing -> Debug.todo "bad must call"

type Interaction = Clicked Id | TextInputted Id String
interactionToProtobuf : Interaction -> Bridge.Interaction
interactionToProtobuf interaction =
    case interaction of
        Clicked id -> Bridge.Interaction <| Just <| Bridge.InteractionKindClick {elementId = id}
        TextInputted id value -> Bridge.Interaction <| Just <| Bridge.InteractionKindTextInput {elementId = id, value = value}

type Element
    = Ref Id
    | Text String
    | Tag {tagname : String, attributes : List (Attribute Msg), children : (List Element)}
tagFromProtobuf : Bridge.Tag -> Element
tagFromProtobuf tag =
    let attributes = must tag.attributes in
    Tag
        { tagname = tag.tagname
        , attributes = attributes.misc |> Dict.toList |> List.map (\(k, v) -> attribute k v)
        , children = tag.children
            |> (\x -> case x of Bridge.TagChildren childrenList -> childrenList)
            |> List.map elementFromProtobuf
        }
elementFromProtobuf : Bridge.Element -> Element
elementFromProtobuf {elementKind} =
    case elementKind of
        Bridge.ElementElementKind Nothing -> Text "invalid protobuf"
        Bridge.ElementElementKind (Just (Bridge.ElementKindRef refId)) -> Ref refId
        Bridge.ElementElementKind (Just (Bridge.ElementKindText text)) -> Text text
        Bridge.ElementElementKind (Just (Bridge.ElementKindTag tag)) -> tagFromProtobuf tag

poll : Timestep -> Cmd Msg
poll ts =
    let
        fromResult : Result Http.Error Bridge.PollResponse -> Msg
        fromResult result = case result of
            Ok {state} -> case state of
                Just bareState -> PollCompleted bareState
                Nothing -> Debug.todo "some kind of error"
            Err err -> PollFailed err
    in
        Http.post
            { url = "/poll"
            , body = Http.bytesBody "application/octet-stream"
                <| Protobuf.Encode.encode
                <| Bridge.toPollRequestEncoder {sinceTimestep = ts}
            , expect = Protobuf.Decode.expectBytes fromResult Bridge.pollResponseDecoder
            }

notify : Interaction -> Cmd Msg
notify interaction =
    Http.post
        { url = "/interaction"
        , body = Http.bytesBody "application/octet-stream"
            <| Protobuf.Encode.encode
            <| Bridge.toInteractionRequestEncoder
                { interaction = Just <| interactionToProtobuf interaction
                }
        , expect = Http.expectWhatever (always Ignore)
        }

init : () -> Url.Url -> navkey -> (Model,  Cmd Msg)
init _ _ _ =
    ( { serverState =
        { elements = Dict.singleton "root" (Text "Loading...")
        , timestep = 0
        , root = "root"
        }
      }
    , poll 0
    )

update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
    case msg of
        Interacted interaction -> (model, notify interaction)
        PollCompleted {timestep, rootId, elements} ->
            let
                oldState = model.serverState
            in
            ( { model | serverState = { oldState
                                        | root = rootId
                                        , elements = oldState.elements |> Dict.union (Dict.map (\_ e -> elementFromProtobuf (must e)) elements)
                                        , timestep = timestep
                                        }
              }
            , poll timestep
            )
        PollFailed err -> Debug.todo (Debug.toString err)
        Ignore -> (model, Cmd.none)

view : Model -> Browser.Document Msg
view model =
    { title="Bridge"
    , body=
        [ case Dict.get model.serverState.root model.serverState.elements of
            Nothing -> text "<NO ROOT?>"
            Just element -> viewElement model.serverState.elements model.serverState.root element
        ]
    }

viewElement : Dict.Dict Id Element -> Id -> Element -> Html Msg
viewElement elements id element =
    case element of
        Text s -> Html.text s
        Tag {tagname, attributes, children} ->
            let
                allAttributes = case tagname of
                    "button" -> onClick (Interacted (Clicked id)) :: attributes
                    "input" -> onInput (\val -> Interacted (TextInputted id val)) :: attributes
                    _ -> attributes
            in
                Html.node tagname allAttributes (List.map (viewElement elements id) children)
        Ref refId -> case Dict.get refId elements of
            Nothing -> text <| "<no such element: " ++ refId ++ ">"
            Just referent -> viewElement elements refId referent

main = Browser.application
    { init=init
    , update=update
    , view=view
    , subscriptions=(always Sub.none)
    , onUrlRequest=(always Ignore)
    , onUrlChange=(always Ignore)
    }
